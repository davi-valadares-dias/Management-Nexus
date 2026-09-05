from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Categoria, Fornecedor, Produto, Movimentacao

admin.site.register(Categoria)
admin.site.register(Fornecedor)
admin.site.register(Produto)
admin.site.register(Movimentacao)