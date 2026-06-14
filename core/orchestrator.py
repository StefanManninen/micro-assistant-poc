import sys
import os
import time

# Add the root folder to sys.path so Python can find the storage module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_ollama import OllamaClient
from storage.database import AssistantDatabase

class Orchestrator:
    def __init__(self):
        self.ai = OllamaClient()
        self.db = AssistantDatabase()
        self.current_context = "server_env"
        
        self.tool_schemas = [
            {
                "name": "browser_search",
                "description": "Search the web for fresh documentation or error messages",
                "parameters": ["query"]
            }
        ]

    def run_loop(self, user_input):
        start_time = time.time()
        
        # 1.CHECK LOCAL STATE IN THE POLICY LAYER (v3)
        policy = self.db.get_policy_state(self.current_context, user_input)
        
        if policy:
            # Case A: Both route selection and response are verified -> Respond immediately in 0 ms
            if policy["route_weight"] >= 2.0 and policy["answer_weight"] >= 2.0:
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000
                self.db.log_intuition_hit(2500 - execution_time_ms, 450)
                
                print(f"\n🚀 [Fast Local Intuition] (Source: {policy['source']})")
                print(f"-> Matched hash. The entire state verified on {execution_time_ms:.2f} ms.")
                return policy["cached_answer"], "local_policy", None

            # Case B: The path choice is known, but the answer is uncertain -> Reuse tools immediately!
            elif policy["route_weight"] >= 2.0 and policy["answer_weight"] < 2.0:
                print("\n🧠 [Route-Intuition]: I know this question requires a tool, but the answer needs to be updated.")
                print("-> Skips gemma3 intent. Activates browser_search directly...")
                
                tool_result = "Solution: Use 'docker compose up -d' for detached mode."
                final_prompt = f"Data: {tool_result}\nAnswer the user's question briefly: {user_input}"
                core_response = self.ai.ask_gemma_core(final_prompt)
                return core_response, "browser_search", "browser_search"

        # 2. STANDARD LOOP (If we don't know anything yet)
        print("\n[No local intuition found] Starting Ollama engines...")
        core_response = self.ai.ask_gemma_core(user_input)
        router_decision = "no_tool"
        tool_used = None
        
        if "don't know" in core_response.lower() or "search" in user_input.lower() or "error message" in user_input.lower():
            print("-> [System]: Information gap detected. Consulting functiongemma...")
            raw_router_decision = self.ai.ask_function_router(user_input, self.tool_schemas)
            
            if "browser_search" in raw_router_decision:
                router_decision = "browser_search"
                tool_used = "browser_search"
                print(f"-> [Router decision]: {router_decision} (Cleaned)")
                
                tool_result = "Solution: Use 'docker compose up -d' for detached mode."
                final_prompt = f"Data: {tool_result}\nAnswer the user's question briefly: {user_input}"
                core_response = self.ai.ask_gemma_core(final_prompt)
            else:
                print("-> [Router decision]: No tool was triggered.")

        return core_response, router_decision, tool_used

if __name__ == "__main__":
    orchestrator = Orchestrator()
    print("=== POC v3: Secure hash matching and model brake ===")
    
    while True:
        try:
            user_text = input(f"\n[{orchestrator.current_context}] $ ").strip()
            if not user_text: continue
            if user_text.lower() in ['exit', 'quit']: break
            
            # Internal commands are handled first, before run_loop()
            if user_text.lower() == 'stats':
                stats = orchestrator.db.get_stats()
                print("\n📊 === ACCUMULATED RESOURCE SAVINGS ===")
                print(f" Intuition Hits (Ollama Skipped): {int(stats['intuition_hits'])} ")
                print(f" Estimated Saved Tokens:         {int(stats['saved_tokens'])} tokens")
                print(f" Estimated Saved Compute Time:   {stats['saved_time_ms']/1000:.2f} seconds")
                print("========================================")
                continue
            
            # Run loop
            response, router_text, tool_used = orchestrator.run_loop(user_text)
            print(f"[Assistant]: {response}")
            
            # If we didn't use perfect local policy, log and ask for feedback
            if router_text != "local_policy":
                orchestrator.db.log_interaction(orchestrator.current_context, user_text, router_text, response)
                
                print("\n--- FEEDBACK ---")
                fb_route = input("Was it the RIGHT CHOICE to use tools/dialogue? (y/n): ").strip().lower()
                fb_ans = input("Was the ANSWER itself good and correct? (y/n): ").strip().lower()
                
                route_rw = 0.5 if fb_route == 'y' else -0.5
                answer_rw = 0.5 if fb_ans == 'y' else -0.5
                
                # Save the differentiated feedback in the database.
                orchestrator.db.initialize_or_update_policy(
                    orchestrator.current_context, 
                    user_text, 
                    response, 
                    route_rw, 
                    answer_rw,
                    source="generated_and_verified" if fb_ans == 'y' else "generated_unverified"
                )
                print("-> Differentiated feedback saved in SQLite v3.")
                    
        except KeyboardInterrupt:
            break
    print("\nExiting and saving environment...")