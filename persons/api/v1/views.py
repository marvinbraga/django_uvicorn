import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import aiohttp
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.views.generic import View
from loguru import logger
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from persons.api.v1.serializers import PersonSerializer
from persons.models import Person


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class CheckPersonAPIView(APIView):

    def get(self, request, *args, **kwargs):
        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.get_person, request)
            response = future.result()
        return response

    def get_person(self, request):
        pk = request.query_params.get('pk', None)
        person = Person.objects.get(pk=pk)
        serializer = PersonSerializer(person)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreatePersonAPIView(APIView):

    def create_persons(self):
        logger.debug("Executando...")
        for i in range(1000):
            Person.objects.create(name=f'Person {i}', age=i)
            sleep(0.5)
        logger.debug("Finalizado...")

    def create_bulk(self, request):
        logger.debug("Iniciando a criação...")
        self.create_persons()
        return Response({"message": "1000 persons created"}, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        logger.debug("Cheguei no GET...")
        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.create_bulk, request)
            response = future.result()
        return response


class AsyncFetchDataAPIView(View):
    async def fetch_data(self, session, url):
        logger.debug("Cheguei no fetch_data...")
        async with session.get(url) as response:
            return await response.json()

    async def get(self, request, *args, **kwargs):
        logger.debug("Cheguei no GET...")
        urls = [
            "https://jsonplaceholder.typicode.com/todos/1",
            "https://jsonplaceholder.typicode.com/todos/2",
            "https://jsonplaceholder.typicode.com/todos/3",
            "https://jsonplaceholder.typicode.com/todos/2",
            "https://jsonplaceholder.typicode.com/todos/1",
        ]
        logger.debug("Iniciando...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_data(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug("Finalizando...")
        return JsonResponse({"results": results})


class AsyncCreatePersonAPIView(View):

    @sync_to_async
    def create_persons(self):
        logger.debug("Executando...")
        for i in range(1000):
            Person.objects.create(name=f'Person {i}', age=i)
        logger.debug("Finalizado...")

    async def create_bulk(self, request):
        logger.debug("Iniciando a criação...")
        await self.create_persons()
        return {"message": "1000 persons created"}

    async def get(self, request, *args, **kwargs):
        logger.debug("Cheguei no GET...")
        logger.debug("Iniciando...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.create_bulk(request)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug("Finalizando...")
        return JsonResponse({"results": results})
