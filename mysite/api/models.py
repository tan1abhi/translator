from django.db import models

# Create your models here.
class BlogPost(models.Model):
    title  = models.CharField(max_length=100)
    content = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)


class Translate(models.Model):
    choices = (("ENGLISH","english"),("HINDI","hindi"),("TAMIL","tamil"))
    language = models.CharField(max_length=10,choices=choices,default="HINDI")
    translated_content= models.TextField(default="HINDI")
    content = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)


class Voice_Translate(models.Model):
    choices = (("ENGLISH","english"),("HINDI","hindi"),("TAMIL","tamil"))
    language = models.CharField(max_length=10,choices=choices,default="HINDI")
    translated_content= models.TextField(default="HINDI")
    content = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)


def __str__(self):
    return self.title 