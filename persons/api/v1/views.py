import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from time import sleep

import aiohttp
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.views.generic import View
from loguru import logger
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError

from persons.api.v1.serializers import PersonSerializer
from persons.models import Person


class PersonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for standard CRUD operations on Person model.
    Includes automatic pagination (configured in settings).
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class CheckPersonAPIView(APIView):
    """
    Sync view using ThreadPoolExecutor to offload blocking ORM operations.
    GET /api/v1/check/?pk=<person_id>
    """

    def get(self, request, *args, **kwargs):
        try:
            with ThreadPoolExecutor() as executor:
                future = executor.submit(self.get_person, request)
                response = future.result()
            return response
        except (ValidationError, NotFound) as e:
            # Re-raise DRF exceptions so they are handled properly
            raise
        except Exception as e:
            logger.error(f"Error in CheckPersonAPIView: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_person(self, request):
        pk = request.query_params.get('pk', None)

        if not pk:
            raise ValidationError("Parameter 'pk' is required")

        try:
            person = Person.objects.get(pk=pk)
            serializer = PersonSerializer(person)
            logger.info(f"Person retrieved: {person.name} (ID: {pk})")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            raise NotFound(f"Person with pk={pk} not found")
        except ValueError:
            raise ValidationError("Invalid pk format")


def thread_pool(func):
    """
    Decorator that wraps a function to run in a ThreadPoolExecutor.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with ThreadPoolExecutor() as executor:
            future = executor.submit(func, *args, **kwargs)
            response = future.result()
        return response

    return wrapper


class CreatePersonAPIView(APIView):
    """
    Sync view with ThreadPoolExecutor decorator for bulk person creation.
    POST /api/v1/create_bulk/
    Body: {"count": <number>}  (max 10000)
    """

    @thread_pool
    def post(self, request, *args, **kwargs):
        try:
            count = request.data.get('count', 10)

            # Validation: limit to prevent abuse
            if not isinstance(count, int) or count < 1:
                return Response(
                    {"error": "Count must be a positive integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if count > 10000:
                return Response(
                    {"error": "Count cannot exceed 10000"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Starting bulk creation of {count} persons...")

            for i in range(count):
                Person.objects.create(name=f'Person {i}', age=(i % 100))
                if count > 100:  # Only sleep for large batches
                    sleep(0.01)  # Reduced sleep time

            logger.info(f"Completed bulk creation of {count} persons")
            return Response(
                {"message": f"{count} persons created successfully"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error in CreatePersonAPIView: {str(e)}")
            return Response(
                {"error": "Failed to create persons"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AsyncFetchDataAPIView(View):
    """
    Pure async view using aiohttp for concurrent HTTP requests.
    GET /api/v1/fetch_data/
    """

    async def fetch_data(self, session, url):
        """Fetch data from a single URL asynchronously."""
        try:
            logger.debug(f"Fetching data from: {url}")
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.json()
                logger.debug(f"Successfully fetched data from: {url}")
                return data
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching data from: {url}")
            return {"error": "Timeout", "url": url}
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {str(e)}")
            return {"error": str(e), "url": url}

    async def get(self, request, *args, **kwargs):
        try:
            logger.info("Starting async data fetch from multiple sources...")

            urls = [
                "https://jsonplaceholder.typicode.com/todos/1",
                "https://jsonplaceholder.typicode.com/todos/2",
                "https://jsonplaceholder.typicode.com/todos/3",
                "https://jsonplaceholder.typicode.com/todos/4",
                "https://jsonplaceholder.typicode.com/todos/5",
            ]

            async with aiohttp.ClientSession() as session:
                tasks = [self.fetch_data(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("Completed async data fetch")
            return JsonResponse({"results": results, "total": len(results)})
        except Exception as e:
            logger.error(f"Error in AsyncFetchDataAPIView: {str(e)}")
            return JsonResponse(
                {"error": "Failed to fetch data"},
                status=500
            )


class AsyncCreatePersonAPIView(View):
    """
    Async view using sync_to_async for bulk person creation.
    POST /api/v1/async_create_bulk/
    Body: {"count": <number>}  (max 10000)
    """

    @sync_to_async
    def create_persons(self, count):
        """Create persons synchronously (wrapped for async use)."""
        persons = []
        for i in range(count):
            persons.append(Person(name=f'Person {i}', age=(i % 100)))

        # Bulk create is much more efficient than individual creates
        Person.objects.bulk_create(persons, batch_size=500)
        logger.info(f"Created {count} persons using bulk_create")

    async def create_bulk(self, count):
        """Wrapper for async context."""
        await self.create_persons(count)
        return {"message": f"{count} persons created successfully"}

    async def post(self, request, *args, **kwargs):
        try:
            # Parse JSON body
            import json
            body = json.loads(request.body.decode('utf-8'))
            count = body.get('count', 10)

            # Validation
            if not isinstance(count, int) or count < 1:
                return JsonResponse(
                    {"error": "Count must be a positive integer"},
                    status=400
                )

            if count > 10000:
                return JsonResponse(
                    {"error": "Count cannot exceed 10000"},
                    status=400
                )

            logger.info(f"Starting async bulk creation of {count} persons...")

            tasks = [self.create_bulk(count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"Completed async bulk creation")
            return JsonResponse({"results": results})
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON in request body"},
                status=400
            )
        except Exception as e:
            logger.error(f"Error in AsyncCreatePersonAPIView: {str(e)}")
            return JsonResponse(
                {"error": "Failed to create persons"},
                status=500
            )
