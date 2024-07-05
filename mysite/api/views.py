from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BlogPost,Translate, Voice_Translate
from .serializers import BlogPostSerializer, TranslateSerializer , Voice_TranslateSerializer
from googletrans import Translator
from .voice_to_text import VoiceToText
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


# Create your views here.

class BlogPostListCreate(generics.ListCreateAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer

    def delete(self,request, *args, **kwargs):
        BlogPost.objects.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BlogPostRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = "pk"




#translate class 

class TranslateListCreate(generics.ListCreateAPIView):
    queryset = Translate.objects.all()
    serializer_class = TranslateSerializer
   

    def delete(self,request, *args, **kwargs):
        Translate.objects.all()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def create(self,request,*args,**kwargs):
        content = request.data.get('content')
        lang = request.data.get('language')
        published_date = request.data.get('published_date')
        if(not content):
            return Response({"error": "content is required"}, status=status.HTTP_400_BAD_REQUEST)
        translator = Translator()
        translated = translator.translate(content,dest=lang).text

        translate_instance = Translate.objects.create(content=content, translated_content=translated, language=lang, published_date=published_date)
        serializer = self.get_serializer(translate_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TranslateRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Translate.objects.all()
    serializer_class = TranslateSerializer
    lookup_field = "pk"

   

class VoiceTranslateListCreate(generics.ListCreateAPIView):
    queryset = Voice_Translate.objects.all()
    serializer_class = Voice_TranslateSerializer

    def create(self,request, *args, **kwargs):
        content = request.data.get('content')
        lang = request.data.get('language')
        published_date = request.data.get('published_date')

        m4a_file = r'C:\Users\hp\OneDrive\Desktop\Symphony No.6 (1st movement).m4a'
        voice_to_text = VoiceToText(m4a_file)
        transcribed_text = voice_to_text.convert_to_text()

        if(not content):
            return Response({"error : no content provided" }, status=status.HTTP_404_NOT_FOUND)
        translator = Translator()
        translated  =translator.translate(content,dest=lang).text
        voice_translate_instance = Voice_Translate.objects.create(content = transcribed_text,  translated_content = translated , language = lang , published_date = published_date)
        serializer = self.get_serializer(voice_translate_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class VoiceTranslateRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Translate.objects.all()
    serializer_class = TranslateSerializer
    lookup_field = "pk"

   
    

@csrf_exempt
def webhook_view(request):
    if request.method == 'GET':
        challenge = request.GET.get('hub.challenge')
        return HttpResponse(challenge if challenge else 'No challenge found')
    elif request.method == 'POST':
        # Process the webhook payload here
        return HttpResponse('Webhook received')
    else:
        return HttpResponse(status=405)