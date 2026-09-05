from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    nome = models.CharField(max_length=150)
    cnpj_cpf = models.CharField(max_length=20, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    codigo_barras = models.CharField(max_length=50, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    unidade_medida = models.CharField(max_length=20)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    estoque_minimo = models.IntegerField(default=5)
    estoque_atual = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sku} - {self.nome}"

class Movimentacao(models.Model):
    TIPO_CHOICES = (
        ('E', 'Entrada'),
        ('S', 'Saída'),
    )
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    data = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    motivo = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Movimentações"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})"

# Regra de negócio: Atualiza o saldo do produto automaticamente
@receiver(post_save, sender=Movimentacao)
def atualizar_estoque(sender, instance, created, **kwargs):
    if created:
        produto = instance.produto
        if instance.tipo == 'E':
            produto.estoque_atual += instance.quantidade
        elif instance.tipo == 'S':
            produto.estoque_atual -= instance.quantidade
        produto.save()