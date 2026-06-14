import sys
import os

# Add the root folder to sys.path so Python can find the storage module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.database import AssistantDatabase

def run_immune_system():
    db = AssistantDatabase()
    print("🧼 [Layer 3: Immune Defense] Starts quality review of local intuition (v3)...")
    
    # Get the new separated columns from v3 policy
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT context_hash, raw_input, cached_answer, route_weight, answer_weight, source 
            FROM tool_policy
        ''')
        rules = cursor.fetchall()
        
    if not rules:
        print("-> No local rules found in the database to review.")
        return

    for context_hash, raw_input, cached_answer, route_weight, answer_weight, source in rules:
        print(f"\n[Reviewing Rule]: '{raw_input}'")
        print(f"->Current status: Route weight: {route_weight}, Answer-weight: {answer_weight}, Source: {source}")
        
        # HEURISTICS TO DETECT AI FEVER (Now updated for v3)
        is_corrupt = False
        reasons = []
        
        # Rule A: Does the text contain broken INI syntax in the middle of everything?
        if "[web-server]" in cached_answer:
            is_corrupt = True
            reasons.append("Found invalid INI syntax '[web-server]' in a YAML/Docker context")
            
        # Rule B: Does the text contain fictional loops around file names?
        if cached_answer.count("docker-compose.json") > 1:
            is_corrupt = True
            reasons.append("Found repetitive loops around non-standard filenames (.json)")
            
        if is_corrupt:
            print(f"⚠️  [CRITIC]: The line was flagged as corrupt! Reason: {', '.join(reasons)}")
            print("-> Summons the Supervisor (Bigger Expert Model) to clear the memory...")
            
            # HERE IS A CALL TO A LARGER EXPERT MODEL OR API SIMULATED
            expert_clean_answer = (
                "Absolutely! When you get error messages in your Docker Compose file, use the flag '--verbose' "
                "to get full debug logs, or '-f' to specify an exact file.\n\n"
                "Run this to troubleshoot:\n"
                "```bash\n"
                "docker compose --verbose up -d\n"
                "```\n"
                "Also check your indentation in the YAML file as incorrect spaces are the most common error.."
            )
            
            # Overwrite the broken memory in SQLite with the expert's clean answer,
            # and raise answer_weight to verified level and stamp the source!
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tool_policy 
                    SET cached_answer = ?, 
                        answer_weight = 2.0, 
                        source = 'verified_expert' 
                    WHERE context_hash = ?
                ''', (expert_clean_answer, context_hash))
                conn.commit()
                
            print("✨ [SUCCESS]:The memory has been washed! The broken text has been replaced with bulletproof expert code.")
        else:
            print("✅ [CRITIC]: Line passed. No syntactic anomalies found.")

if __name__ == "__main__":
    run_immune_system()