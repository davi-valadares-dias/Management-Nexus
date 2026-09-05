from django.core.paginator import Paginator
import csv
import io
import json
from django.http import HttpResponse, FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Produto, Movimentacao
from .forms import MovimentacaoForm, ProdutoForm, CategoriaForm, FornecedorForm

def is_admin(user):
    return user.is_staff


@login_required
@login_required
def dashboard(request):
    query = request.GET.get('q')
    if query:
        produtos_lista = Produto.objects.filter(Q(nome__icontains=query) | Q(sku__icontains=query))
    else:
        produtos_lista = Produto.objects.all()

    # --- LÓGICA DOS CARDS DE RESUMO ---
    total_produtos = produtos_lista.count()
    # Conta quantos produtos estão com estoque baixo
    itens_baixo_estoque = sum(1 for p in produtos_lista if p.estoque_atual <= p.estoque_minimo)
    # Multiplica a quantidade pelo preço para saber o valor em dinheiro no estoque
    valor_total_estoque = sum(p.estoque_atual * p.preco_venda for p in produtos_lista)

    # --- LÓGICA DA PAGINAÇÃO ---
    paginator = Paginator(produtos_lista, 15)  # Mostra 15 produtos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'page_obj': page_obj,  # Enviamos a página atual em vez da lista inteira
        'query': query,
        'total_produtos': total_produtos,
        'itens_baixo_estoque': itens_baixo_estoque,
        'valor_total_estoque': valor_total_estoque
    }
    return render(request, 'estoque/dashboard.html', contexto)


@login_required
def nova_movimentacao(request):
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.usuario = request.user
            movimentacao.save()
            return redirect('dashboard')
    else:
        form = MovimentacaoForm()

    return render(request, 'estoque/movimentacao.html', {'form': form})


@user_passes_test(is_admin)
@login_required
def novo_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProdutoForm()

    return render(request, 'estoque/produto.html', {'form': form})


@login_required
def historico_movimentacoes(request):
    # O sinal de menos (-) faz a ordenação do mais novo para o mais velho
    movimentacoes = Movimentacao.objects.all().order_by('-data')
    return render(request, 'estoque/historico.html', {'movimentacoes': movimentacoes})


@user_passes_test(is_admin)
@login_required
def exportar_relatorio_csv(request):
    # Avisa o navegador que é um arquivo UTF-8
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="relatorio_estoque.csv"'

    # Adiciona o BOM (identificador de caracteres) para o Excel corrigir os acentos (ç, ã, ô)
    response.write('\ufeff')

    # Altera o delimitador para ponto e vírgula (;), que é o padrão do Excel no Brasil
    writer = csv.writer(response, delimiter=';')

    # Escreve o cabeçalho
    writer.writerow(['SKU', 'Produto', 'Categoria', 'Preço de Custo', 'Preço de Venda', 'Estoque Atual', 'Status'])

    produtos = Produto.objects.all()

    # Escreve as linhas substituindo o ponto da casa decimal por vírgula para ficar 100% no padrão BR
    for produto in produtos:
        status = 'Estoque Baixo' if produto.estoque_atual <= produto.estoque_minimo else 'Normal'
        writer.writerow([
            produto.sku,
            produto.nome,
            produto.categoria.nome if produto.categoria else 'Sem Categoria',
            str(produto.preco_custo).replace('.', ','),
            str(produto.preco_venda).replace('.', ','),
            produto.estoque_atual,
            status
        ])

    return response

    return response


@user_passes_test(is_admin)
@login_required
def editar_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    if request.method == 'POST':
        # O "instance=produto" avisa o formulário para preencher os dados antigos e atualizar
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProdutoForm(instance=produto)
    return render(request, 'estoque/produto.html', {'form': form})


@user_passes_test(is_admin)
@login_required
def excluir_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    produto.delete()
    return redirect('dashboard')


@user_passes_test(is_admin)
@login_required
def exportar_relatorio_pdf(request):
    # Cria o PDF na memória
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "Relatório Geral de Estoque")

    # Cabeçalho da Tabela
    p.setFont("Helvetica-Bold", 12)
    y = 760
    p.drawString(50, y, "SKU")
    p.drawString(130, y, "Produto")
    p.drawString(380, y, "Preço")
    p.drawString(480, y, "Qtd Atual")
    y -= 20

    # Linhas dos Produtos
    p.setFont("Helvetica", 11)
    produtos = Produto.objects.all()
    for produto in produtos:
        p.drawString(50, y, str(produto.sku))
        p.drawString(130, y, str(produto.nome)[:40])  # Corta nomes gigantes
        p.drawString(380, y, f"R$ {produto.preco_venda}")
        p.drawString(480, y, str(produto.estoque_atual))
        y -= 20
        # Cria uma página nova se chegar no fim do papel
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 11)
            y = 800

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='relatorio.pdf')
@user_passes_test(is_admin)
@login_required
def nova_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CategoriaForm()
    # Passamos um 'titulo' para o HTML saber qual tela está abrindo
    return render(request, 'estoque/form_basico.html', {'form': form, 'titulo': 'Cadastrar Categoria'})

@user_passes_test(is_admin)
@login_required
def novo_fornecedor(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = FornecedorForm()
    return render(request, 'estoque/form_basico.html', {'form': form, 'titulo': 'Cadastrar Fornecedor'})


@login_required
def relatorio_graficos(request):
    from .models import Categoria
    import json

    categorias = Categoria.objects.all()
    graficos = []

    for cat in categorias:
        # Pega os 15 produtos com maior estoque de cada categoria
        produtos = Produto.objects.filter(categoria=cat).order_by('-estoque_atual')[:15]

        if produtos.exists():
            nomes = [p.nome[:15] + '...' if len(p.nome) > 15 else p.nome for p in produtos]
            quantidades = [p.estoque_atual for p in produtos]

            graficos.append({
                'id': f'grafico_{cat.id}',
                'titulo': f'Estoque - {cat.nome}',
                'nomes': nomes,
                'quantidades': quantidades
            })

    return render(request, 'estoque/graficos.html', {'graficos_json': json.dumps(graficos)})