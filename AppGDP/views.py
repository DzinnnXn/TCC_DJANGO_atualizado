from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from .forms import FormLogin, formCadastroUsuario, InventarioForm, SalaForm
from .models import Senai
from django.contrib.auth.models import User, Group
from .models import Inventario, Sala
from django.core.cache import cache
from django.http import HttpResponse
from .models import Inventario
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from rest_framework.response import Response
from django.http import JsonResponse
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes

# Create your views here.

def homepage(request):
    return render(request, 'homepage.html')

def login(request):
    return render(request, 'login.html')


def profile(request):
    return render(request, 'profile.html')

def faq(request):
    return render(request, 'faq.html')

from django.contrib.auth.models import Group

#logouut 
def logout(request):
    auth_logout(request)
    return redirect('login')

@login_required
def welcomeHomepage(request):
    sala = Sala.objects.all()
    sala_especifica = sala.first()
    
    # Verificar se o usuário pertence ao grupo 'Coordenador' ou 'Professor'
    is_coordenador = request.user.groups.filter(name="Coordenador").exists()
    is_professor = request.user.groups.filter(name="Professor").exists()

    
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('welcomeHomepage')
    else:
        form = SalaForm()

    sala = Sala.objects.all()
    

    return render(request, 'welcomeHomepage.html', {
        'form': form, 
        'sala': sala, 
        'sala_especifica': sala_especifica,
        'is_coordenador': is_coordenador,  # Passa a informação se é coordenador
        'is_professor': is_professor,  # Passa a informação se é professor
    })

# Importar o modelo de itens (substitua Item pelo nome correto do seu modelo)

#---------------------------- CRUD DE SALAS ----------------------------
@login_required
def buscar_salas(request):
    context = {}
    query = request.GET.get('q')
    ordem = request.GET.get('ordem')
    is_coordenador = request.user.groups.filter(name="Coordenador").exists()
    is_professor = request.user.groups.filter(name="Professor").exists()

    sala = Sala.objects.all()

    if query:
        sala = sala.filter(sala__icontains=query)
    
    if ordem:
        sala = sala.order_by('sala' if ordem == 'A-Z' else '-sala')

    context['sala'] = sala
    form = SalaForm()
    context['form'] = form
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor

    return render(request, 'salas.html', context)

@login_required
def buscar_itens_sala(request):
    context = {}
    query = request.GET.get('q')  
    ordem = request.GET.get('ordem')  
    sala = request.GET.get('sala') 
    is_coordenador = request.user.groups.filter(name="Coordenador").exists()
    is_professor = request.user.groups.filter(name="Professor").exists() 

    inventario = Inventario.objects.all()

    if query:
        inventario = inventario.filter(num_inventario__icontains=query)
    
    if ordem:
        inventario = inventario.order_by('denominacao' if ordem == 'A-Z' else '-denominacao')

    if sala:
        inventario = inventario.filter(sala__icontains=sala)

    context['inventario'] = inventario
    form = InventarioForm()
    context['form'] = form
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor

    return render(request, 'itens.html', context)

@login_required
def adicionar_salas(request):
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('welcomeHomepage')
    else:
        form = SalaForm()

    sala = Sala.objects.all()
    
    return render(request, 'welcomeHomepage.html', {'form': form, 'sala': sala})

@login_required
def update_sala(request):
    if request.method == 'POST':
        sala = request.POST.get('sala')
        
        # Busca a sala no banco de dados
        sala = get_object_or_404(Sala, sala=sala)

        # Atualiza os valores com base nos dados do formulário
        sala.descricao = request.POST.get('descricao')
        sala.localizacao = request.POST.get('localizacao')
        sala.link_imagem = request.POST.get('link_imagem')	
        sala.responsavel = request.POST.get('responsavel')
        sala.quantidade_itens = request.POST.get('quantidade_itens')
        sala.save()

        # Redireciona de volta à página de salas ou para onde você quiser
        return redirect('salas')  

    return HttpResponse("Método não permitido.", status=405)

@login_required
def excluir_sala(request):
    if request.method == 'POST':
        sala = request.POST.get('sala')
        
        # Exclui a sala com base no nome
        try:
            sala = Sala.objects.get(sala=sala)
            sala.delete()
            return redirect('salas')  # Redireciona para a lista de salas após exclusão
        except Sala.DoesNotExist:
            return HttpResponse("Sala não encontrada.", status=404)

@login_required
def salas(request):
    is_coordenador = request.user.groups.filter(name="Coordenador").exists()
    is_professor = request.user.groups.filter(name="Professor").exists()
    sala = Sala.objects.all()
    sala_especifica = sala.first()  # ou qualquer outro critério para escolher a sala

    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('salas')  # Redireciona para a página de salas
    else:
        form = SalaForm()
    
    return render(request, 'salas.html', {'form': form, 'sala': sala, 'sala_especifica': sala_especifica, 'is_coordenador': is_coordenador, 'is_professor': is_professor})

#---------------------------- LOGIN E CADASTRO DE USUÁRIO ----------------------------
@login_required
def cadastroUsuario(request):
    context = {}
    dadosSenai = Senai.objects.all()
    context["dadosSenai"] = dadosSenai
    
    if request.method == 'POST':
        form = formCadastroUsuario(request.POST)
        if form.is_valid():
            var_nome = form.cleaned_data['first_name']
            var_sobrenome = form.cleaned_data['last_name']
            var_usuario = form.cleaned_data['user']
            var_email = form.cleaned_data['email']
            var_senha = form.cleaned_data['password']
            var_grupo = form.cleaned_data['group']  # Captura o grupo selecionado

            # Cria o usuário
            user = User.objects.create_user(username=var_usuario, email=var_email, password=var_senha)
            user.first_name = var_nome
            user.last_name = var_sobrenome
            user.save()

            # Atribui o usuário ao grupo selecionado
            grupo = Group.objects.get(name=var_grupo)
            user.groups.add(grupo)

            return redirect('/welcomeHomepage')
            print('Cadastro realizado com sucesso')
    else:
        form = formCadastroUsuario()
        context['form'] = form
        print('Cadastro falhou')
    
    return render(request, 'cadastroUsuario.html', context)

def login(request):
    context = {}
    dadosSenai = Senai.objects.all()
    context["dadosSenai"] = dadosSenai
    if request.method == 'POST':
        form = FormLogin(request.POST)
        if form.is_valid():

            var_usuario = form.cleaned_data['user']
            var_senha = form.cleaned_data['password']
            
            user = authenticate(username=var_usuario, password=var_senha)

            if user is not None:
                auth_login(request, user)
                return redirect('/welcomeHomepage')  
            else:
                print('Login falhou')
    else:
        form = FormLogin()
        context['form'] = form
        return render(request, 'login.html', context)
    
#---------------------------- CRUD DE INVENTÁRIO ----------------------------
@login_required
def itens(request):
    inventario = Inventario.objects.all()
    item_especifico = inventario.first()  # ou qualquer outro critério para escolher o item
    is_coordenador = request.user.groups.filter(name="Coordenador").exists()
    is_professor = request.user.groups.filter(name="Professor").exists()
   
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('itens')  # Redireciona para a página de itens
    else:
        form = InventarioForm()
    
    return render(request, 'itens.html', {'form': form, 'inventario': inventario, 'item_especifico': item_especifico, 'is_coordenador': is_coordenador, 'is_professor': is_professor})

@login_required
def adicionar_inventario(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirecionar para a rota inicial, independente de onde estava
    else:
        form = InventarioForm()
    
    # Se precisar listar todos os itens no modal de adição, inclua isso:
    inventario = Inventario.objects.all()
    
    return render(request, 'itens.html', {'form': form, 'inventario': inventario})

@login_required
def buscar_itens(request):
    context = {}
    query = request.GET.get('q')  # Pega o valor do campo de busca
    ordem = request.GET.get('ordem')  # Pega o valor da ordem A-Z ou Z-A
    sala = request.GET.get('sala')  # Pega o valor da sala
    is_coordenador = request.user.groups.filter(name="Coordenador").exists()
    is_professor = request.user.groups.filter(name="Professor").exists()

    inventario = Inventario.objects.all()

    if query:
        inventario = inventario.filter(num_inventario__icontains=query)
    
    if ordem:
        if ordem == 'A-Z':
            inventario = inventario.order_by('denominacao')
        elif ordem == 'Z-A':
            inventario = inventario.order_by('-denominacao')

    if sala:
        inventario = inventario.filter(sala__icontains=sala)

    context['inventario'] = inventario
    form = InventarioForm()
    context['form'] = form
    context['is_coordenador'] = is_coordenador
    context['is_professor'] = is_professor
    
    return render(request, 'itens.html', context)

@login_required
def update_item(request):
    if request.method == 'POST':
        num_inventario = request.POST.get('numInventario')
        
        # Busca o item no banco de dados
        item = get_object_or_404(Inventario, num_inventario=num_inventario)

        # Atualiza os valores com base nos dados do formulário
        item.denominacao = request.POST.get('denominacao')
        item.localizacao = request.POST.get('localizacao')
        item.sala = request.POST.get('sala')
        item.link_imagem = request.POST.get('imagem')
        item.save()

        # Redireciona de volta à página de itens ou para onde você quiser
        return redirect('itens')  

    return HttpResponse("Método não permitido.", status=405)
@login_required
def excluir_inventario(request):
    if request.method == 'POST':
        num_inventario = request.POST.get('numInventario')
        
        # Exclui o item com base no número de inventário
        try:
            item = Inventario.objects.get(num_inventario=num_inventario)
            item.delete()
            return redirect('itens')  # Redireciona para a lista de itens após exclusão
        except Inventario.DoesNotExist:
            return HttpResponse("Item não encontrado.", status=404)
        
        
        
#---------------------------- FUNÇÕES DA API ----------------------------
@api_view(['POST'])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Autenticação do usuário
    user = authenticate(username=username, password=password)

    if user is not None:
        # Verificar se o usuário pertence ao grupo 'Coordenador' ou 'Professor'
        if user.groups.filter(name="Coordenador").exists():
            user_type = "Coordenador"
        elif user.groups.filter(name="Professor").exists():
            user_type = "Professor"
        else:
            user_type = "Outro"  # Caso o usuário não pertença a nenhum desses grupos

        # Autenticação bem-sucedida
        return Response({
            "message": "Login bem-sucedido", 
            "user": user.username,
            "user_type": user_type ,
            "first_name": user.first_name,
        })
    else:
        # Falha na autenticação
        return Response({"error": "Credenciais inválidas"}, status=400)

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_salas(request):
    """
    View para retornar todas as salas em formato JSON.
    """
    salas = Sala.objects.all().values('id', 'sala', 'descricao', 'localizacao', 'link_imagem', 'responsavel', 'quantidade_itens')
    return Response(list(salas), status=200)

@api_view(['GET'])
def get_inventarios(request):
    """
    View para retornar todos os inventários em formato JSON.
    """
    inventarios = Inventario.objects.all().values(
        'id', 
        'num_inventario',  # Aqui estão os campos do seu modelo
        'denominacao', 
        'localizacao', 
        'link_imagem', 
        'sala'
    )
    return Response(list(inventarios), status=200)

@api_view(['POST'])
def add_inventario(request):
    """
    View para adicionar um novo inventário (patrimônio) no banco de dados.
    """
    try:
        data = json.loads(request.body)  # Tenta carregar o JSON
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Dados inválidos ou mal formatados'}, status=400)

    denominacao = data.get('denominacao')
    localizacao = data.get('localizacao')
    sala = data.get('sala')
    link_imagem = data.get('link_imagem')
    num_inventario = data.get('num_inventario')

    # Validar os dados recebidos
    if not denominacao or not localizacao or not sala or not num_inventario:
        return JsonResponse({'message': 'Dados faltando'}, status=400)

    # Criar o inventário (patrimônio)
    inventario = Inventario.objects.create(
        denominacao=denominacao,
        localizacao=localizacao,
        sala=sala,
        link_imagem=link_imagem,
        num_inventario=num_inventario
    )

    return JsonResponse({'message': 'Inventário adicionado com sucesso!'}, status=201)