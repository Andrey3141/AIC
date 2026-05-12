import os
import time
import yaml
import threading

PROMPTS_FOLDER = "prompts"

class Orchestrator:
    def __init__(self, lm_client, log, employees, on_message=None):
        self.lm = lm_client
        self.log = log
        self.history = []
        self.employees = employees
        self.memory = {emp["token"]: [] for emp in employees}
        self.on_message = on_message

    def _read_prompt(self, filename):
        path = os.path.join(PROMPTS_FOLDER, filename)
        if not os.path.exists(path):
            return f"[{filename} не найден]"

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data.get("prompt", "")

    def run_pipeline(self, user_message, files_content=None):
        stop_signal = False
        max_steps = 10
        step = 0
        all_responses = {}
        last_distribution = {}
    
        self.history.append(("USER", user_message))

        current_batch = [("USER", user_message)]
        final_response = None

        while step < max_steps:
            step += 1
            # === 1. DISTRIBUTOR ===
            self.log(f"=== ШАГ {step} ===", "info")
            distributor_prompt = self._read_prompt(
                next(e for e in self.employees if e["token"] == "DISTRIBUTOR")["prompt"]
            )
            distributor_prompt = self.lm.inject_employees(distributor_prompt, self.employees)

            context = self._build_global_context(limit=1)
            # context = ""
            
            dist_input = f"""{distributor_prompt}
            
ШАГ: {step}

=== КОНТЕКСТ ===
{context}

=== НОВЫЕ СООБЩЕНИЯ ===
{self._format_messages(current_batch)}
"""

            self.log(f"PIPE INPUT: {dist_input.replace(chr(10), '\\n')}", "info")
            dist_response = self.lm.send_message(dist_input)
            
            if not dist_response:
                self.log("DISTRIBUTOR → пустой ответ", "error")
                break
    
            parsed = self._parse_distribution(dist_response)
            
            send_target = None
            for role, action in parsed.items():
                s_t = role.strip().replace("[", "").replace("]", "").upper()
                if action == "send" and s_t == "USER":
                    send_target = s_t
                    break
            
            last_distribution = parsed
            
            self.log(f"DISTRIBUTOR → parsed: {parsed}", "info")

            # === СТОП ===
            if "USER" in parsed and parsed["USER"] == "send" and step > 1:
                stop_signal = True

            self.log(f"Запуск сотрудников: {parsed}", "info")
            
            # === РАСПРЕДЕЛЕНИЕ В ПАМЯТЬ (send + save) ===
            for role, action in parsed.items():
                role = role.strip().replace("[", "").replace("]", "").upper()

                if action in ["send", "save"]:
                    for sender_role, msg in current_batch:
                        self.memory[role].append(
                            f"ВХОД:\n[{sender_role}]: {msg}"
                        )

            # === 2. ЗАПУСК СОТРУДНИКОВ ===
            results = []

            for emp in self.employees:
                role = emp["token"].strip().upper()
    
                if role != "USER" and parsed.get(role) == "send":
                    role = emp["token"]

                    prompt_file = emp.get("prompt")

                    if not prompt_file:
                        continue

                    prompt = self._read_prompt(prompt_file)
                    prompt = self.lm.inject_employees(prompt, self.employees)

                    memory = self._build_memory_context(role)
                    context = self._build_global_context(limit=25)

                    input_text = f"""{prompt}

ШАГ: {step}
РОЛЬ: {role}

=== ОБЩИЙ КОНТЕКСТ ===
{context}

=== КОНТЕКСТ СОТРУДНИКА ===
{memory}

=== ВХОД ===
{self._format_messages(current_batch)}
"""

                    response = self.lm.send_message(input_text)

                    if response:
                        all_responses[role] = response
                        if self.on_message:
                            self.on_message(role, response, last_distribution)

                        self.log(f"{role} → ответ ({len(response)} символов)", "success")

                        self.history.append((role, response))

                        self.memory[role].append(
                            f"ВХОД:\n{self._format_messages(current_batch)}\nОТВЕТ:\n{response}"
                        )

                        results.append((role, response))
                        
            if send_target == "USER":
                self.log("⏳ Ожидание ответа пользователя", "info")
                final_response = None
                break
            elif not results:
                self.log("❌ results пустой — pipeline сломан", "error")
                break
                
            if stop_signal:
                final_response = self._collect_last_messages(results if results else current_batch)
                break

            if not results:
                self.log("Нет новых ответов, остановка", "warning")
                break
                
            # защита от зацикливания на USER
            if results == current_batch:
                self.log("⚠️ current_batch не изменился — цикл", "warning")
                break

            current_batch = results
            
        if step >= max_steps:
            self.log("Достигнут лимит шагов", "warning")

        return {
            "final": final_response or "Нет ответа",
            "history": self.history,
            "responses": all_responses,
            "distribution": last_distribution
        }

    def _parse_distribution(self, text):
        result = {}
        for line in text.splitlines():
            if ":" in line:
                try:
                    role, action = line.split(":")
                    role = role.strip().replace("[", "").replace("]", "").upper()

                    if role == "DISTRIBUTOR":
                        continue

                    result[role] = action.strip()
                except:
                    pass
        return result
        
    def _build_global_context(self, limit=10):
        recent = self.history[-limit:]
        return "\n".join([f"[{role}]: {msg}" for role, msg in recent])
        
    def _build_memory_context(self, role, limit=5):
        mem = self.memory.get(role, [])[-limit:]
        return "\n".join(mem)
        
    def _format_messages(self, messages):
        return "\n".join([f"[{r}]: {m}" for r, m in messages])
        
    def _collect_last_messages(self, batch):
        return "\n".join([f"[{r}]: {m}" for r, m in batch])
