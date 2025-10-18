# import os
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional, List
# import sqlite3
# from datetime import datetime
# import requests
# import json
# import random
# from datetime import datetime

# # Optional LangChain/OpenAI imports
# try:
#     from langchain import OpenAI, LLMChain, PromptTemplate
#     from langchain.chains.conversation.memory import ConversationBufferMemory
# except Exception:
#     OpenAI = None
#     LLMChain = None
#     PromptTemplate = None
#     ConversationBufferMemory = None

# DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
#         id INTEGER PRIMARY KEY,
#         department TEXT,
#         description TEXT,
#         assignee TEXT,
#         assigned_agent TEXT,
#         status TEXT,
#         created_at TEXT
#     )""")
#     cur.execute("""CREATE TABLE IF NOT EXISTS agents (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         specialties TEXT
#     )""")
#     cur.execute("""CREATE TABLE IF NOT EXISTS chat_logs (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         task_id INTEGER,
#         role TEXT,
#         message TEXT,
#         ts TEXT
#     )""")

#     cur.execute("""CREATE TABLE IF NOT EXISTS resources (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT,
#     category TEXT,
#     quantity INTEGER,
#     allocated_to TEXT,
#     status TEXT,
#     created_at TEXT
# )""")
#     # Seed agents
#     cur.execute("SELECT COUNT(*) FROM agents")
#     if cur.fetchone()[0] == 0:
#         agents = [
#             (1, 'Agent-Alice', 'research,communication'),
#             (2, 'Agent-Bob', 'logistics,resource-sharing'),
#             (3, 'Agent-Charlie', 'scheduling,task-assignment'),
#         ]
#         cur.executemany("INSERT INTO agents(id,name,specialties) VALUES (?,?,?)", agents)
#     conn.commit()
#     conn.close()

# def crewai_assign(department, description, assignee):
#     """
#     Simulated CrewAI agent assignment.
#     Picks an agent based on keywords and load balancing.
#     """
#     agents = query_db("SELECT id, name, specialties FROM agents")
    
#     # Score agents by specialty match
#     keywords = (department + ' ' + (description or '')).lower()
#     best_score = -1
#     best_agents = []

#     # Heuristic scoring
#     for r in agents:
#         specialties = r[2] or ''
#         score = sum(1 for s in specialties.split(',') if s.strip() in keywords)
#         if score > best_score:
#             best_score = score
#             best_agents = [r]
#         elif score == best_score:
#             best_agents.append(r)

#     # If multiple agents tie, pick the one with fewest active tasks
#     if best_agents:
#         agent_task_counts = {a[1]: query_db(
#             "SELECT COUNT(*) FROM tasks WHERE assigned_agent = ? AND status != 'COMPLETED'", (a[1],), fetchone=True)[0]
#             for a in best_agents
#         }
#         best_agents.sort(key=lambda a: agent_task_counts.get(a[1], 0))
#         selected = best_agents[0]
#     else:
#         # fallback to agent with fewest active tasks
#         agent_task_counts = {a[1]: query_db(
#             "SELECT COUNT(*) FROM tasks WHERE assigned_agent = ? AND status != 'COMPLETED'", (a[1],), fetchone=True)[0]
#             for a in agents
#         }
#         agents.sort(key=lambda a: agent_task_counts.get(a[1], 0))
#         selected = agents[0]

#     return selected[1]



# init_db()

# app = FastAPI(title='Agentic Collaboration Platform (AI-Ready)')

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class TaskIn(BaseModel):
#     department: str
#     description: str
#     assignee: Optional[str] = None


# class MessageIn(BaseModel):
#     role: Optional[str] = "user"
#     message: str


# def query_db(query, params=(), fetchone=False, commit=False):
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute(query, params)
#     if commit:
#         conn.commit()
#         conn.close()
#         return None
#     rows = cur.fetchall()
#     conn.close()
#     return rows[0] if fetchone and rows else rows


# @app.get('/tasks')
# def get_tasks(search: Optional[str] = None):
#     if search:
#         rows = query_db("SELECT id,department,description,assignee,assigned_agent,status,created_at FROM tasks WHERE description LIKE ?", (f"%{search}%",))
#     else:
#         rows = query_db("SELECT id,department,description,assignee,assigned_agent,status,created_at FROM tasks ORDER BY id DESC")
#     return [dict(id=r[0], department=r[1], description=r[2], assignee=r[3], assigned_agent=r[4], status=r[5], created_at=r[6]) for r in rows]


# @app.post('/tasks')
# def create_task(payload: TaskIn):
#     ts = datetime.utcnow().isoformat()
#     query_db("INSERT INTO tasks(department,description,assignee,status,created_at) VALUES (?,?,?,?,?)",
#              (payload.department, payload.description, payload.assignee, 'OPEN', ts), commit=True)
#     rows = query_db("SELECT id,department,description,assignee,assigned_agent,status,created_at FROM tasks ORDER BY id DESC")
#     r = rows[0]
#     return dict(id=r[0], department=r[1], description=r[2], assignee=r[3], assigned_agent=r[4], status=r[5], created_at=r[6])


# @app.post('/assign/{task_id}')
# def assign_task(task_id: int):
#     row = query_db("SELECT id,department,description,assignee FROM tasks WHERE id = ?", (task_id,), fetchone=True)
#     if not row:
#         raise HTTPException(status_code=404, detail='Task not found')
#     _, department, description, assignee = row

#     # Use simulated CrewAI
#     selected_agent = crewai_assign(department, description, assignee)

#     query_db("UPDATE tasks SET assigned_agent = ?, status = ? WHERE id = ?",
#              (selected_agent, 'ASSIGNED', task_id), commit=True)
#     log_chat(task_id, 'system', f"Task assigned to {selected_agent} (simulated CrewAI)")
#     return {"task_id": task_id, "assigned_agent": selected_agent}


# def pick_agent_heuristic(department, description):
#     rows = query_db("SELECT id,name,specialties FROM agents")
#     keywords = (department + ' ' + description).lower()
#     best = None
#     best_score = 0
#     for r in rows:
#         specialties = r[2] or ''
#         score = sum(1 for s in specialties.split(',') if s.strip() in keywords)
#         if score > best_score:
#             best_score = score
#             best = r
#     return best[1] if best else rows[0][1]


# def log_chat(task_id, role, message):
#     ts = datetime.utcnow().isoformat()
#     query_db("INSERT INTO chat_logs(task_id,role,message,ts) VALUES (?,?,?,?)", (task_id, role, message, ts), commit=True)


# @app.get('/chat/{task_id}')
# def get_chat(task_id: int):
#     rows = query_db("SELECT id,role,message,ts FROM chat_logs WHERE task_id = ? ORDER BY id ASC", (task_id,))
#     return [{"id": r[0], "role": r[1], "message": r[2], "ts": r[3]} for r in rows]


# @app.post('/chat/{task_id}')
# async def post_chat(task_id: int, payload: MessageIn):
#     rows = query_db("SELECT id FROM tasks WHERE id = ?", (task_id,), fetchone=True)
#     if not rows:
#         raise HTTPException(status_code=404, detail="Task not found")
#     log_chat(task_id, payload.role or 'user', payload.message)

#     openai_key = os.environ.get('AIzaSyAIVSgMkuJl7Cj-hKCY_xnVca41TWvEjNI')
#     response_text = None
#     if openai_key and OpenAI is not None:
#         try:
#             logs = query_db("SELECT role,message FROM chat_logs WHERE task_id = ? ORDER BY id DESC LIMIT 10", (task_id,))
#             convo = "\n".join([f"{r[0]}: {r[1]}" for r in logs[::-1]])
#             template = """You are an AI assistant helping with cross-department collaboration tasks. Use the conversation history below and reply helpfully and concisely.\n\n{history}\nUser: {user}\nAssistant:"""
#             prompt = PromptTemplate(template=template, input_variables=["history", "user"])
#             memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)
#             llm = OpenAI(temperature=0.2, openai_api_key=openai_key)
#             chain = LLMChain(llm=llm, prompt=prompt)
#             result = chain.run(history=convo, user=payload.message)
#             response_text = result
#         except Exception as e:
#             response_text = f"[LangChain/OpenAI error: {str(e)}]"
#     else:
#         response_text = f"Agent (simulated): I received your message about '{payload.message[:80]}'. I'll coordinate with the assigned agent."

#     log_chat(task_id, 'assistant', response_text)
#     return {"reply": response_text}

# @app.get('/agents')
# def get_agents():
#     rows = query_db("SELECT id, name, specialties FROM agents")
#     return [{"id": r[0], "name": r[1], "specialties": r[2]} for r in rows]

# # Get all resources
# @app.get('/resources')
# def get_resources():
#     rows = query_db("SELECT id, name, category, quantity, allocated_to, status, created_at FROM resources ORDER BY id DESC")
#     return [dict(id=r[0], name=r[1], category=r[2], quantity=r[3],
#                  allocated_to=r[4], status=r[5], created_at=r[6]) for r in rows]

# # Add new resource
# @app.post('/resources')
# def add_resource(resource: dict):
#     ts = datetime.utcnow().isoformat()
#     query_db("INSERT INTO resources(name, category, quantity, allocated_to, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
#              (resource["name"], resource["category"], resource["quantity"],
#               resource.get("allocated_to", None), resource.get("status", "AVAILABLE"), ts), commit=True)
#     return {"detail": "Resource added successfully"}

# # Allocate resource to a department
# @app.post('/allocate/{resource_id}')
# def allocate_resource(resource_id: int, payload: dict):
#     department = payload.get("department")
#     if not department:
#         raise HTTPException(status_code=400, detail="Department required for allocation.")
#     query_db("UPDATE resources SET allocated_to = ?, status = ? WHERE id = ?",
#              (department, "ALLOCATED", resource_id), commit=True)
#     return {"detail": f"Resource {resource_id} allocated to {department}"}

# # Release resource
# @app.post('/release/{resource_id}')
# def release_resource(resource_id: int):
#     query_db("UPDATE resources SET allocated_to = NULL, status = ? WHERE id = ?",
#              ("AVAILABLE", resource_id), commit=True)
#     return {"detail": f"Resource {resource_id} released and marked as available"}


# @app.get('/agent_messages/{agent_name}')
# def get_agent_messages(agent_name: str):
#     # Fetch all tasks assigned to this agent
#     tasks = query_db("SELECT id FROM tasks WHERE assigned_agent = ?", (agent_name,))
#     task_ids = [t[0] for t in tasks]
#     all_logs = []
#     for tid in task_ids:
#         logs = query_db("SELECT role,message,ts FROM chat_logs WHERE task_id = ? ORDER BY id ASC", (tid,))
#         for l in logs:
#             all_logs.append({"task_id": tid, "role": l[0], "message": l[1], "ts": l[2]})
#     # Sort by timestamp
#     all_logs.sort(key=lambda x: x['ts'])
#     return all_logs

# # DELETE a task
# @app.delete('/tasks/{task_id}')
# def delete_task(task_id: int):
#     row = query_db("SELECT id FROM tasks WHERE id = ?", (task_id,), fetchone=True)
#     if not row:
#         raise HTTPException(status_code=404, detail="Task not found")
#     query_db("DELETE FROM tasks WHERE id = ?", (task_id,), commit=True)
#     query_db("DELETE FROM chat_logs WHERE task_id = ?", (task_id,), commit=True)
#     return {"detail": f"Task {task_id} deleted successfully"}

# def pick_agent_heuristic(department, description):
#     # Fetch all agents
#     agents = query_db("SELECT id, name, specialties FROM agents")
    
#     # Count active tasks per agent
#     agent_task_counts = {}
#     for a in agents:
#         count = query_db("SELECT COUNT(*) FROM tasks WHERE assigned_agent = ? AND status != 'COMPLETED'", (a[1],), fetchone=True)[0]
#         agent_task_counts[a[1]] = count

#     keywords = (department + ' ' + description).lower()
#     best_score = -1
#     best_agents = []

#     # First, score agents by specialty match
#     for r in agents:
#         specialties = r[2] or ''
#         score = sum(1 for s in specialties.split(',') if s.strip() in keywords)
#         if score > best_score:
#             best_score = score
#             best_agents = [r]
#         elif score == best_score:
#             best_agents.append(r)

#     # If multiple agents tie, pick the one with fewest active tasks
#     if best_agents:
#         best_agents.sort(key=lambda a: agent_task_counts.get(a[1],0))
#         selected = best_agents[0]
#     else:
#         # fallback to agent with fewest active tasks
#         agents.sort(key=lambda a: agent_task_counts.get(a[1],0))
#         selected = agents[0]

#     return selected[1]  # return agent name

# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)


import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from datetime import datetime
import requests
import json
import random

# Optional LangChain/OpenAI imports
try:
    from langchain import OpenAI, LLMChain, PromptTemplate
    from langchain.chains.conversation.memory import ConversationBufferMemory
except Exception:
    OpenAI = None
    LLMChain = None
    PromptTemplate = None
    ConversationBufferMemory = None

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        department TEXT,
        description TEXT,
        assignee TEXT,
        assigned_agent TEXT,
        status TEXT,
        created_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY,
        name TEXT,
        specialties TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        role TEXT,
        message TEXT,
        ts TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        quantity INTEGER,
        allocated_to TEXT,
        status TEXT,
        created_at TEXT
    )""")
    
    # Seed agents
    cur.execute("SELECT COUNT(*) FROM agents")
    if cur.fetchone()[0] == 0:
        agents = [
            (1, 'Agent-Alice', 'research,communication'),
            (2, 'Agent-Bob', 'logistics,resource-sharing'),
            (3, 'Agent-Charlie', 'scheduling,task-assignment'),
        ]
        cur.executemany("INSERT INTO agents(id,name,specialties) VALUES (?,?,?)", agents)
    conn.commit()
    conn.close()

def crewai_assign(department, description, assignee):
    """
    Simulated CrewAI agent assignment.
    Picks an agent based on keywords and load balancing.
    """
    agents = query_db("SELECT id, name, specialties FROM agents")
    
    # Score agents by specialty match
    keywords = (department + ' ' + (description or '')).lower()
    best_score = -1
    best_agents = []

    # Heuristic scoring
    for r in agents:
        specialties = r[2] or ''
        score = sum(1 for s in specialties.split(',') if s.strip() in keywords)
        if score > best_score:
            best_score = score
            best_agents = [r]
        elif score == best_score:
            best_agents.append(r)

    # If multiple agents tie, pick the one with fewest active tasks
    if best_agents:
        agent_task_counts = {a[1]: query_db(
            "SELECT COUNT(*) FROM tasks WHERE assigned_agent = ? AND status != 'COMPLETED'", (a[1],), fetchone=True)[0]
            for a in best_agents
        }
        best_agents.sort(key=lambda a: agent_task_counts.get(a[1], 0))
        selected = best_agents[0]
    else:
        # fallback to agent with fewest active tasks
        agent_task_counts = {a[1]: query_db(
            "SELECT COUNT(*) FROM tasks WHERE assigned_agent = ? AND status != 'COMPLETED'", (a[1],), fetchone=True)[0]
            for a in agents
        }
        agents.sort(key=lambda a: agent_task_counts.get(a[1], 0))
        selected = agents[0]

    return selected[1]


init_db()

app = FastAPI(title='Agentic Collaboration Platform (AI-Ready)')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskIn(BaseModel):
    department: str
    description: str
    assignee: Optional[str] = None


class MessageIn(BaseModel):
    role: Optional[str] = "user"
    message: str


def query_db(query, params=(), fetchone=False, commit=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    if commit:
        conn.commit()
        conn.close()
        return None
    rows = cur.fetchall()
    conn.close()
    return rows[0] if fetchone and rows else rows


@app.get('/tasks')
def get_tasks(search: Optional[str] = None):
    if search:
        rows = query_db("SELECT id,department,description,assignee,assigned_agent,status,created_at FROM tasks WHERE description LIKE ?", (f"%{search}%",))
    else:
        rows = query_db("SELECT id,department,description,assignee,assigned_agent,status,created_at FROM tasks ORDER BY id DESC")
    return [dict(id=r[0], department=r[1], description=r[2], assignee=r[3], assigned_agent=r[4], status=r[5], created_at=r[6]) for r in rows]


@app.post('/tasks')
def create_task(payload: TaskIn):
    ts = datetime.utcnow().isoformat()
    query_db("INSERT INTO tasks(department,description,assignee,status,created_at) VALUES (?,?,?,?,?)",
             (payload.department, payload.description, payload.assignee, 'OPEN', ts), commit=True)
    rows = query_db("SELECT id,department,description,assignee,assigned_agent,status,created_at FROM tasks ORDER BY id DESC")
    r = rows[0]
    return dict(id=r[0], department=r[1], description=r[2], assignee=r[3], assigned_agent=r[4], status=r[5], created_at=r[6])


@app.post('/assign/{task_id}')
def assign_task(task_id: int):
    row = query_db("SELECT id,department,description,assignee FROM tasks WHERE id = ?", (task_id,), fetchone=True)
    if not row:
        raise HTTPException(status_code=404, detail='Task not found')
    _, department, description, assignee = row

    # Use simulated CrewAI
    selected_agent = crewai_assign(department, description, assignee)

    query_db("UPDATE tasks SET assigned_agent = ?, status = ? WHERE id = ?",
             (selected_agent, 'ASSIGNED', task_id), commit=True)
    log_chat(task_id, 'system', f"Task assigned to {selected_agent} (simulated CrewAI)")
    return {"task_id": task_id, "assigned_agent": selected_agent}


def pick_agent_heuristic(department, description):
    rows = query_db("SELECT id,name,specialties FROM agents")
    keywords = (department + ' ' + description).lower()
    best = None
    best_score = 0
    for r in rows:
        specialties = r[2] or ''
        score = sum(1 for s in specialties.split(',') if s.strip() in keywords)
        if score > best_score:
            best_score = score
            best = r
    return best[1] if best else rows[0][1]


def log_chat(task_id, role, message):
    ts = datetime.utcnow().isoformat()
    query_db("INSERT INTO chat_logs(task_id,role,message,ts) VALUES (?,?,?,?)", (task_id, role, message, ts), commit=True)


@app.get('/chat/{task_id}')
def get_chat(task_id: int):
    rows = query_db("SELECT id,role,message,ts FROM chat_logs WHERE task_id = ? ORDER BY id ASC", (task_id,))
    return [{"id": r[0], "role": r[1], "message": r[2], "ts": r[3]} for r in rows]


@app.post('/chat/{task_id}')
async def post_chat(task_id: int, payload: MessageIn):
    rows = query_db("SELECT id FROM tasks WHERE id = ?", (task_id,), fetchone=True)
    if not rows:
        raise HTTPException(status_code=404, detail="Task not found")
    log_chat(task_id, payload.role or 'user', payload.message)

    openai_key = os.environ.get('OPENAI_API_KEY')
    response_text = None
    if openai_key and OpenAI is not None:
        try:
            logs = query_db("SELECT role,message FROM chat_logs WHERE task_id = ? ORDER BY id DESC LIMIT 10", (task_id,))
            convo = "\n".join([f"{r[0]}: {r[1]}" for r in logs[::-1]])
            template = """You are an AI assistant helping with cross-department collaboration tasks. Use the conversation history below and reply helpfully and concisely.\n\n{history}\nUser: {user}\nAssistant:"""
            prompt = PromptTemplate(template=template, input_variables=["history", "user"])
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)
            llm = OpenAI(temperature=0.2, openai_api_key=openai_key)
            chain = LLMChain(llm=llm, prompt=prompt)
            result = chain.run(history=convo, user=payload.message)
            response_text = result
        except Exception as e:
            response_text = f"[LangChain/OpenAI error: {str(e)}]"
    else:
        response_text = f"Agent (simulated): I received your message about '{payload.message[:80]}'. I'll coordinate with the assigned agent."

    log_chat(task_id, 'assistant', response_text)
    return {"reply": response_text}


@app.get('/agents')
def get_agents():
    rows = query_db("SELECT id, name, specialties FROM agents")
    return [{"id": r[0], "name": r[1], "specialties": r[2]} for r in rows]


# Get all resources
@app.get('/resources')
def get_resources():
    rows = query_db("SELECT id, name, category, quantity, allocated_to, status, created_at FROM resources ORDER BY id DESC")
    return [dict(id=r[0], name=r[1], category=r[2], quantity=r[3],
                 allocated_to=r[4], status=r[5], created_at=r[6]) for r in rows]


# Add new resource
@app.post('/resources')
def add_resource(resource: dict):
    ts = datetime.utcnow().isoformat()
    query_db("INSERT INTO resources(name, category, quantity, allocated_to, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
             (resource["name"], resource["category"], resource["quantity"],
              resource.get("allocated_to", None), resource.get("status", "AVAILABLE"), ts), commit=True)
    return {"detail": "Resource added successfully"}


# Allocate resource to a department
@app.post('/allocate/{resource_id}')
def allocate_resource(resource_id: int, payload: dict):
    department = payload.get("department")
    if not department:
        raise HTTPException(status_code=400, detail="Department required for allocation.")
    query_db("UPDATE resources SET allocated_to = ?, status = ? WHERE id = ?",
             (department, "ALLOCATED", resource_id), commit=True)
    return {"detail": f"Resource {resource_id} allocated to {department}"}


# Release resource
@app.post('/release/{resource_id}')
def release_resource(resource_id: int):
    query_db("UPDATE resources SET allocated_to = NULL, status = ? WHERE id = ?",
             ("AVAILABLE", resource_id), commit=True)
    return {"detail": f"Resource {resource_id} released and marked as available"}


@app.get('/agent_messages/{agent_name}')
def get_agent_messages(agent_name: str):
    # Fetch all tasks assigned to this agent
    tasks = query_db("SELECT id FROM tasks WHERE assigned_agent = ?", (agent_name,))
    task_ids = [t[0] for t in tasks]
    all_logs = []
    for tid in task_ids:
        logs = query_db("SELECT role,message,ts FROM chat_logs WHERE task_id = ? ORDER BY id ASC", (tid,))
        for l in logs:
            all_logs.append({"task_id": tid, "role": l[0], "message": l[1], "ts": l[2]})
    # Sort by timestamp
    all_logs.sort(key=lambda x: x['ts'])
    return all_logs


# DELETE a task
@app.delete('/tasks/{task_id}')
def delete_task(task_id: int):
    row = query_db("SELECT id FROM tasks WHERE id = ?", (task_id,), fetchone=True)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    query_db("DELETE FROM tasks WHERE id = ?", (task_id,), commit=True)
    query_db("DELETE FROM chat_logs WHERE task_id = ?", (task_id,), commit=True)
    return {"detail": f"Task {task_id} deleted successfully"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)