from rest_framework import serializers
from .models import BlogPost,Translate,Voice_Translate

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ["id","title","content","published_date"]

class TranslateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translate
        fields = ["id","language","content","published_date","translated_content"]


class Voice_TranslateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voice_Translate
        fields = ["id","language","content","published_date","translated_content"]