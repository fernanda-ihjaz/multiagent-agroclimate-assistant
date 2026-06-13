# Assistente Agroclimático Multiagente
Projeto final de Inteligência Artificial: um sistema multiagente com LLMs locais (Ollama),
RAG e MCP para apoio à decisão agroclimática (trigo/soja) na região de Passo Fundo (RS).
## 👥 Equipe
- Fernanda Japur Ihjaz
- Érica Pilati Sartoreto
- Maria Eduarda Schell
## 🚀 Tecnologias e Pré-requisitos
- **Python 3.10+**
- **Ollama** (modelos recomendados: `llama3.1:8b` ou `mistral`)
- **Gerenciador de pacotes:** `pip`
## ⚙️ Instalação e Configuração
1. **Clone o repositório:**
```bash
git clone https://github.com/fernanda-ihjaz/multiagent-agroclimate-assistant.git
cd multiagent-agroclimate-assistant
```
2. **Crie e ative um ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate # No Windows: venv\Scripts\activate
```
3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```
4. **Inicie o Ollama e certifique-se de baixar o modelo local:**
```bash
ollama serve
ollama pull llama3.1
```
## 📂 Estrutura do Repositório

A estrutura de diretórios é a seguinte:
```text
multiagent-agroclimate-assistant/
├── data/           # Dados brutos (INMET), PDFs de domínio (docs) e banco vetorial
│
(vectorstore)
│
├── examples/       # Exemplos de uso e cenários de testes
│
├── scripts/        # Scripts utilitários de ingestão e indexação
│ │
│ ├── index_knowledge_base.py
│ └── ingest_inmet.py
│
├── src/            # Código fonte principal
│ │
│ ├── agents/       # Lógica dos agentes (orquestrador, climatologia, RAG, risco, revisor)
│ ├── mcp_servers/  # Servidores MCP (clima, RAG, relatórios)
│ ├── rag/          # Mecanismo de RAG (embeddings, loader, retriever)
│ ├── tools/        # Ferramentas individuais utilizadas pelos agentes
│ └── utils/        # Utilitários gerais (logger, parser)
│
├── tests/          # Testes automatizados (test_indices.py, test_rag.py)
│
├── config.py       # Configurações globais da aplicação
│
├── main.py         # Ponto de entrada e Interface CLI (Typer)
│
└── requirements.txt # Lista de dependências Python
```
## 💻 Como Usar (CLI)
O sistema foi desenhado para ser executado integralmente via terminal através do
`main.py`. Abaixo estão os comandos principais:
**1. Indexar a Base de Conhecimento (RAG):**
Antes da primeira execução, é necessário criar o banco vetorial a partir dos documentos
técnicos.
```bash
python main.py indexar
```
**2. Consulta Livre:**
Faça perguntas em linguagem natural para o assistente.
```bash
python main.py consultar "há risco de geada na floração do trigo nos últimos 30 dias?"
```
**3. Análise Estruturada:**
Execute análises passando parâmetros diretos.
```bash
python main.py analisar --cultura trigo --fase floracao --periodo "ultimos-30-dias"
```
**4. Explicação Técnica (Apenas RAG):**
Consulte diretamente a literatura técnica (Embrapa/ZARC) sem envolver cálculo de dados.

```bash
python main.py explicar "o que favorece giberela no trigo?"
```
**5. Modo Demonstração:**
Executa cenários pré-configurados para validação e apresentação.
```bash
python main.py demo
```
## 🧠 Arquitetura e Fluxo de Agentes
O sistema é coordenado por um **Orquestrador** que delega as tarefas para agentes
especialistas:
- **Agente Climatológico:** Processa séries históricas do INMET e calcula índices
(graus-dia, horas de frio, etc.).
- **Agente Recuperador (RAG):** Busca referências e limiares técnicos nos documentos
indexados.
- **Agente Avaliador de Risco:** Cruza os dados climáticos calculados com as regras do
RAG.
- **Agente Revisor:** Valida se a resposta tem sentido agronômico e se os dados e fontes
não foram alucinados.