# Sistema de Gerenciamento de Pacientes

Sistema backend desenvolvido em FastAPI para gerenciamento de dados médicos de pacientes, com arquitetura de microserviços, autenticação JWT e funcionalidades de busca avançada.

## 🚀 Início Rápido

### Pré-requisitos

- Docker Desktop instalado e rodando
- PowerShell (Windows) ou Terminal (Linux/Mac)
- 4GB RAM disponível
- Portas 8000-8003, 5432 e 6379 livres

### Instalação (Windows PowerShell)

```powershell
# 1. Clone o repositório
git clone https://github.com/GMussolini/synthea-data-system.git
cd synthea-data-system

# 2. Build dos containers
docker-compose build --no-cache

# 3. Iniciar os serviços
docker-compose up -d

# 4. Verificar se todos estão rodando
docker-compose ps
```

### Verificação da Instalação

Após cerca de 30 segundos, verifique se todos os serviços estão rodando:

```powershell
docker-compose ps
```

Você deve ver algo assim:
```
NAME                IMAGE                              STATUS          PORTS
patient-db          postgres:15-alpine                 Up (healthy)    0.0.0.0:5432->5432/tcp
patient-redis       redis:7-alpine                     Up (healthy)    0.0.0.0:6379->6379/tcp
auth-service        synthea-data-system-auth-service  Up              0.0.0.0:8001->8000/tcp
patient-service     synthea-data-system-patient-...   Up              0.0.0.0:8002->8000/tcp
search-service      synthea-data-system-search-...    Up              0.0.0.0:8003->8000/tcp
patient-gateway     nginx:alpine                       Up              0.0.0.0:8000->80/tcp
```

### Popular o Banco com Dados de Teste

```powershell
# Aguarde os serviços iniciarem completamente (30 segundos)
Start-Sleep -Seconds 30

# Execute o script de seed
docker-compose exec patient-service python scripts/seed_data.py --all
```

## 📋 Características

- ✅ **Arquitetura de Microserviços** com estrutura modular
- ✅ **API RESTful** com FastAPI
- ✅ **Autenticação JWT** com refresh tokens
- ✅ **CRUD Completo** de pacientes
- ✅ **Busca Avançada** com múltiplos filtros e scoring
- ✅ **Validação Brasileira** (CPF, CEP, telefone)
- ✅ **Documentação Swagger** automática
- ✅ **Testes Automatizados** isolados por serviço
- ✅ **Docker Compose** para orquestração
- ✅ **Logging JSON** estruturado
- ✅ **Health Checks** em cada serviço
- ✅ **Rate Limiting** via Nginx
- ✅ **API Gateway** centralizado

## 🏗️ Arquitetura

### Estrutura dos Serviços

```
patient-management-system/
│
├── auth-service/               # Serviço de autenticação
│   ├── models/                 # Modelos do banco
│   ├── schemas/                # Validações Pydantic
│   ├── routers/                # Endpoints da API
│   ├── utils/                  # Utilitários
│   ├── tests/                  # Testes do serviço
│   ├── main.py                 # Aplicação principal
│   ├── database.py             # Configuração do BD
│   └── requirements.txt        # Dependências
│
├── patient-service/            # Serviço de pacientes
│   ├── models/                 # Modelos do banco
│   ├── schemas/                # Validações Pydantic
│   ├── routers/                # Endpoints da API
│   ├── utils/                  # Utilitários
│   ├── tests/                  # Testes do serviço
│   ├── scripts/                # Scripts auxiliares
│   ├── main.py                 # Aplicação principal
│   ├── database.py             # Configuração do BD
│   └── requirements.txt        # Dependências
│
├── search-service/             # Serviço de busca
│   ├── models/                 # Modelos do banco
│   ├── schemas/                # Validações Pydantic
│   ├── routers/                # Endpoints da API
│   ├── utils/                  # Utilitários
│   ├── tests/                  # Testes do serviço
│   ├── main.py                 # Aplicação principal
│   ├── database.py             # Configuração do BD
│   └── requirements.txt        # Dependências
│
├── docker-compose.yml          # Orquestração
├── nginx.conf                  # API Gateway
└── README.md                   # Esta documentação
```

### Portas dos Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| API Gateway | 8000 | Nginx - Ponto de entrada único |
| Auth Service | 8001 | Autenticação JWT |
| Patient Service | 8002 | CRUD de pacientes |
| Search Service | 8003 | Busca avançada |
| PostgreSQL | 5432 | Banco de dados |
| Redis | 6379 | Cache |

## 🔐 Autenticação

### Credenciais de Teste

Após executar o `seed_data.py`:

| Usuário | Username | Password | Tipo |
|---------|----------|----------|------|
| Admin | admin | admin123 | Administrador |
| User | user | user123 | Usuário comum |
| Doctor | doctor | doctor123 | Médico |

### Exemplos de Uso

#### 1. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

#### 2. Criar Paciente
```bash
curl -X POST "http://localhost:8000/patients" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "name": "João Silva",
    "cpf": "12345678901",
    "birth_date": "1990-01-01",
    "gender": "M",
    "email": "joao@example.com",
    "medical_conditions": ["Diabetes", "Hipertensão"]
  }'
```

#### 3. Buscar Pacientes
```bash
# Busca simples
curl "http://localhost:8000/search/patients?name=João"

# Busca avançada
curl "http://localhost:8000/search/patients?condition=Diabetes&age_min=30&age_max=50"
```

## 📚 Endpoints da API

### Autenticação
- `POST /auth/register` - Registrar usuário
- `POST /auth/login` - Login
- `POST /auth/refresh` - Renovar token
- `GET /auth/me` - Dados do usuário
- `POST /auth/verify` - Verificar token

### Pacientes
- `GET /patients` - Listar pacientes
- `GET /patients/{id}` - Buscar por ID
- `POST /patients` - Criar paciente
- `PUT /patients/{id}` - Atualizar paciente
- `DELETE /patients/{id}` - Deletar paciente
- `POST /patients/import` - Importar JSON
- `GET /patients/stats/summary` - Estatísticas

### Busca
- `GET /search/patients` - Busca avançada
- `GET /search/suggestions` - Sugestões autocomplete

### Monitoramento
- `GET /health` - Health check (todos os serviços)

## 🧪 Testes

### Executar Todos os Testes
```powershell
# Auth Service
docker-compose exec auth-service pytest tests/ -v

# Patient Service
docker-compose exec patient-service pytest tests/ -v

# Search Service
docker-compose exec search-service pytest tests/ -v
```

### Com Cobertura
```powershell
docker-compose exec patient-service pytest --cov=. --cov-report=html
```

## 🛠️ Comandos Úteis

### Logs
```powershell
# Ver todos os logs
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f patient-service
```

### Reiniciar Serviços
```powershell
# Reiniciar tudo
docker-compose restart

# Reiniciar um serviço
docker-compose restart patient-service
```

### Limpar e Reconstruir
```powershell
# Parar e limpar tudo
docker-compose down -v

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

## 📊 Modelo de Dados

### Tabela: patients
```sql
- id (UUID)
- name (String)
- cpf (String, único)
- birth_date (Date)
- gender (String)
- email (String)
- phone (String)
- address (JSON)
- medical_conditions (JSON Array)
- medications (JSON Array)
- allergies (JSON Array)
- emergency_contact (JSON)
- insurance_info (JSON)
- notes (Text)
- created_at (DateTime)
- updated_at (DateTime)
```

### Tabela: users
```sql
- id (UUID)
- email (String, único)
- username (String, único)
- full_name (String)
- hashed_password (String)
- is_active (Boolean)
- is_admin (Boolean)
- created_at (DateTime)
- updated_at (DateTime)
```

## 🐛 Resolução de Problemas

### Container PostgreSQL não inicia
```powershell
docker-compose down -v
docker volume prune -f
docker-compose up -d
```

### Erro "uvicorn not found"
Certifique-se de que os arquivos `requirements.txt` existem em cada pasta de serviço e execute:
```powershell
docker-compose build --no-cache
```

### Serviços não conectam ao banco
Aguarde 30 segundos após iniciar para o banco estar pronto:
```powershell
Start-Sleep -Seconds 30
docker-compose ps
```

## 👥 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para dúvidas ou problemas, abra uma issue no GitHub.
