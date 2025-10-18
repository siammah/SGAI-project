import os
import logging
import random
from groq import Groq

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = "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"


def get_round_summary(round_actions, round_states, round_roles, round_images, round_score=None, timeout=10):
    """
    Generate a dramatic newspaper-style summary of the round using the LLM. 
    Provides ALL data points from the round including role, state, posture, weather, and time of day for each image, along with the user's action.
    Returns the summary string, or 'summary unavailable' on error.
    Logs the full API response and prints the summary to the console as it streams.
    The summary is formatted for display in a UI box, with clear line breaks between sections.
    """

    # Count zombies vs. humans
    zombie_count = 0
    human_count = 0
    for state, count in round_states.items():
        if state == 'zombie':
            zombie_count += count
        else:
            human_count += count
    
    # Use the actual round score if provided, otherwise calculate from round data
    if round_score:
        humans_saved = round_score.get('humans_saved', 0)
        humans_killed = round_score.get('humans_killed', 0)
        zombies_saved = round_score.get('zombies_saved', 0)
        zombies_killed = round_score.get('zombies_killed', 0)
        corpses_encountered = round_score.get('corpses_encountered', 0)
    else:
        # Fallback calculation from round data
        humans_saved = 0
        humans_killed = 0
        zombies_saved = 0
        zombies_killed = 0
        corpses_encountered = 0
        
        for img_fp, action, state, role in round_images:
            if action == 'save':
                if state == 'zombie':
                    zombies_saved += 1
                elif state == 'corpse':
                    corpses_encountered += 1
                else:  # human (healthy, injured, etc.)
                    humans_saved += 1
            elif action == 'squish':
                if state == 'zombie':
                    zombies_killed += 1
                elif state == 'corpse':
                    corpses_encountered += 1
                else:  # human
                    humans_killed += 1
            elif action == 'skip':
                if state == 'corpse':
                    corpses_encountered += 1
                # Skip doesn't count as killing for humans/zombies

    # Build structured round events list for easy AI processing
    round_events = []
    for i, (img_fp, action, state, role) in enumerate(round_images, 1):
        # Create structured event format with essential information only
        event_desc = f"EVENT {i}: {action.upper()} | {role} | {state}"
        round_events.append(event_desc)

    # Build the prompt with ALL data points
    prompt = f"""You are a dramatic news reporter in a zombie apocalypse simulation. A full round has just ended in a game where the player is an ambulance driver.  
During the round, the player encountered multiple humans and zombies in different roles and took various actions including:
- save (attempt to save the entity and bring them into the ambulance),
- squish (kill the entity),
- scram (return to the hospital and drop off saved passengers and emptying capacity. there is no negative connotation to this action),
- skip (do nothing).

SCORING SYSTEM:
- Humans Saved: Count of humans successfully rescued (save action)
- Humans Killed: Count of humans killed by player (squish action only)
- Zombies Saved: Count of zombies brought into ambulance (save action)
- Zombies Killed: Count of zombies eliminated by player (squish action only)
- Corpses Encountered: Count of corpses seen during the round (any action)
- Skip Action: Does NOT count as killing - just choosing not to help

IMPORTANT: These are the FIVE MAIN COUNTS that determine player performance:
1. Humans Saved (positive score): {humans_saved}
2. Humans Killed (negative score): {humans_killed}
3. Zombies Saved (controversial - saving zombies): {zombies_saved}
4. Zombies Killed (positive score): {zombies_killed}
5. Corpses Encountered: {corpses_encountered}

Entities encountered included elderly (grandpas), doctors, business people, police, and corpses — some were humans, others were zombies. 

Below is COMPLETE data from the round, including:
- Summary counts of actions taken (how many times each action was performed)
- Summary counts of states encountered (how many humans, zombies, injured, healthy, corpses were seen)
- Summary counts of roles encountered (how many doctors, elderly, business, police were encountered)
- EVERY SINGLE EVENT from the round in structured format: EVENT # | ACTION | ROLE | STATE

Your job:  
Write a SHORT dramatic, emotionally charged newspaper-style summary of the round's events. You may occasionally be satirical, witty, or mocking if the player's actions warrant it 
(e.g., saving a zombie, killing a doctor, etc.). 

PROCESSING INSTRUCTIONS:
1. Scan the events chronologically to understand the player's decision pattern
2. Identify the most impactful or controversial actions (e.g., saving zombies, killing doctors, etc.)
3. Count key statistics: humans saved vs killed, zombies saved vs killed
4. Look for patterns: did they prioritize certain roles? Did they make tactical errors?

Mention key figures (elderly, doctors, police, business people, corpses),
 consequences (mass human casualties, saving tons of zombies), 
 and the impact of the player's actions.

Output format:
Headline: [Format the headline in Markdown as a level 1 heading, e.g., # Headline, so it can be rendered as large and bold in the UI. Write a dramatic, emotionally charged headline.]
Focus: [A short phrase (2-5 words) describing the main focus or connotation of the article. Use EXACTLY one of these keywords: 'squished doctor', 'squished elderly', 'squished business', 'squished police', 'squished zombie', 'saved zombie', 'saved doctor', 'saved elderly', 'saved business', 'saved police', 'scrammed everyone', 'skipped everyone', 'saved everyone', 'no actions taken'. This should match the player's most impactful or controversial action.]
[Then, on the next line, write a short (4–6 sentence) article, AROUND 100 WORDS, excerpt in the tone of a media outlet. Do NOT prefix this with 'Blurb:' or any label. Just write the blurb text directly.] THIS SUMMARY MUST BE SHORT AND CONCISE. USE NUMBERS AND STATISTICS TO MAKE IT MORE DRAMATIC, WHEN APPLICABLE.

ROUND STATISTICS:  
Actions taken: {round_actions}  
States encountered: {round_states}  
Roles encountered: {round_roles}  
Zombies seen: {zombie_count}  
Humans seen: {human_count}  

CHRONOLOGICAL EVENTS (in order of occurrence):
{chr(10).join(round_events)}
"""

    api_key = GROQ_API_KEY
    if not api_key:
        print("[Groq] GROQ_API_KEY not set in environment.")
        return "summary unavailable"

    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
            timeout=timeout,
        )
        summary = ""
        print("[Groq Streaming Summary]: ", end="", flush=True)
        for chunk in completion:
            # Each chunk is a partial response
            content = getattr(chunk.choices[0].delta, 'content', None)
            if content:
                print(content, end="", flush=True)
                summary += content
        print()  # Newline after streaming
        # Log the summary (streaming doesn't give a single full response object)
        print(f"[Groq Final Summary]: {summary}")
        return summary.strip() if summary.strip() else "summary unavailable"
    except Exception as e:
        print(f"[Groq] API call failed: {e}")
        return "summary unavailable" 


def get_final_game_summary(final_score, total_rounds, timeout=10):
    """
    Generate a dramatic newspaper-style summary of the entire game using the LLM.
    Returns the summary string, or 'summary unavailable' on error.
    """
    
    # Build the prompt for the final game summary
    prompt = f"""You are a dramatic news reporter in a zombie apocalypse simulation. A complete game has just ended where the player was an ambulance driver across {total_rounds} rounds.

CRITICAL ZOMBIE CONTAMINATION MECHANICS: 
- Saving a zombie creates IMMEDIATE contamination - all humans currently in the ambulance are killed instantly
- Any humans saved AFTER a zombie is in the ambulance are immediately killed by zombie contamination
- The ambulance becomes a death trap until it's cleared via scram
- This creates a devastating cascade effect where one zombie can kill many humans

FINAL GAME STATISTICS:
- Humans Saved: {final_score.get('humans_saved', 0)}
- Humans Killed: {final_score.get('humans_killed', 0)}
- Zombies Saved: {final_score.get('zombies_saved', 0)}
- Zombies Killed: {final_score.get('zombies_killed', 0)}
- Total Rounds: {total_rounds}

Your job:  
Write a SHORT dramatic, emotionally charged newspaper-style summary of the entire game's events. You may occasionally be satirical, witty, or mocking if the player's actions warrant it.
Mention the overall performance, key statistics, and the devastating impact of the player's actions across all rounds.

EMPHASIS ON ZOMBIE CONTAMINATION: If the player saved any zombies, highlight the catastrophic consequences across the entire game.

Output format:
Headline: [Format the headline in Markdown as a level 1 heading, e.g., # Headline, so it can be rendered as large and bold in the UI. Write a dramatic, emotionally charged headline.]
Focus: [A short phrase (2-5 words) describing the main focus or connotation of the article. Use EXACTLY one of these keywords: 'squished military', 'squished doctor', 'squished elderly', 'squished business', 'squished zombie', 'saved zombie', 'saved military', 'saved doctor', 'saved elderly', 'saved business', 'scrammed everyone', 'skipped everyone', 'saved everyone', 'no actions taken'. This should match the player's most impactful or controversial action across the entire game.]
[Then, on the next line, write a short (4–6 sentence) article, AROUND 100 WORDS, excerpt in the tone of a media outlet. Do NOT prefix this with 'Blurb:' or any label. Just write the blurb text directly.] THIS SUMMARY MUST BE SHORT AND CONCISE. USE NUMBERS AND STATISTICS TO MAKE IT MORE DRAMATIC, WHEN APPLICABLE.
"""

    api_key = GROQ_API_KEY
    if not api_key:
        print("[Groq] GROQ_API_KEY not set in environment.")
        return "summary unavailable"
    
    try:
        client = Groq(api_key=api_key)
        
        # Use the same model and settings as get_round_summary
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
            timeout=timeout
        )
        
        summary = ""
        print("[Groq Streaming Final Summary]: ", end="", flush=True)
        for chunk in response:
            # Each chunk is a partial response
            content = getattr(chunk.choices[0].delta, 'content', None)
            if content:
                print(content, end="", flush=True)
                summary += content
        print()  # Newline after streaming
        # Log the summary (streaming doesn't give a single full response object)
        print(f"[Groq Final Summary]: {summary}")
        return summary.strip() if summary.strip() else "summary unavailable"
        
    except Exception as e:
        print(f"[Groq] Error generating final game summary: {e}")
        return "summary unavailable"


def get_image_caption_groq(focus, summary_blurb=None, timeout=10):
    """
    Generate a short, dramatic, and descriptive caption for an image representing the given focus.
    The caption should intensify the tone of the summary, be punchy, and no more than 15 words.
    Returns the caption string, or 'caption unavailable' on error.
    """
    prompt = f"""
    You are a dramatic, witty, and creative news caption writer for a zombie apocalypse ambulance game.
    Write a very short caption that describes an image that represents the following focus from a game round: "{focus}".
    The caption should intensify the tone of the following summary: "{summary_blurb}".
    Make it concise and no more than 10 words. Start with Pictured Above: [Text]. Do not use generic phrases. Do not prefix with 'Caption:' DO NOT INCLUDE QUOTATION MARKS.
    """
    api_key = GROQ_API_KEY
    if not api_key:
        print("[Groq] GROQ_API_KEY not set in environment.")
        return "caption unavailable"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
            timeout=timeout,
        )
        # Extract the caption from the response
        message = getattr(completion.choices[0], 'message', None)
        caption = getattr(message, 'content', None) if message else None
        if caption:
            caption = caption.strip()
        print(f"[Groq Image Caption]: {caption}")
        return caption if caption else "caption unavailable"
    except Exception as e:
        print(f"[Groq] API call for caption failed: {e}")
        return "caption unavailable"


def get_final_game_summary(final_score, total_rounds, all_game_events=None, all_round_actions=None, all_round_states=None, all_round_roles=None, timeout=10):
    """
    Generate a dramatic commander's report summary of the entire game.
    Provides a military-style debrief of the player's performance.
    Returns the summary string, or 'summary unavailable' on error.
    """
    
    # Extract key statistics
    humans_saved = final_score.get('humans_saved', 0)
    humans_killed = final_score.get('humans_killed', 0)
    zombies_saved = final_score.get('zombies_saved', 0)
    zombies_killed = final_score.get('zombies_killed', 0)
    corpses_encountered = final_score.get('corpses_encountered', 0)
    
    # Calculate performance metrics
    total_humans_encountered = humans_saved + humans_killed
    total_zombies_encountered = zombies_saved + zombies_killed
    rescue_ratio = humans_saved / max(total_humans_encountered, 1)
    
    # Calculate comprehensive game statistics
    total_actions = sum(all_round_actions.values()) if all_round_actions else 0
    total_entities = sum(all_round_states.values()) if all_round_states else 0
    total_roles = sum(all_round_roles.values()) if all_round_roles else 0
    avg_actions_per_round = total_actions / total_rounds if total_rounds > 0 else 0
    
    # Build structured game events list for easy AI processing
    game_events = []
    if all_game_events:
        for i, (img_fp, action, state, role, round_num) in enumerate(all_game_events, 1):
            # Create structured event format with round number
            event_desc = f"EVENT {i} (ROUND {round_num}): {action.upper()} | {role} | {state}"
            game_events.append(event_desc)
    
    # Build the prompt
    prompt = f"""You are a military commander delivering a final mission report for a zombie apocalypse ambulance operation.

MISSION STATISTICS:
- Casualties Prevented: {humans_saved}
- Friendly Fire Incidents: {humans_killed}
- Zombies Saved: {zombies_saved}
- Zombie Eliminations: {zombies_killed}
- Corpses Encountered: {corpses_encountered}
- Total Rounds Completed: {total_rounds}
- Rescue Success Rate: {rescue_ratio:.1%}

GAME ACTIVITY SUMMARY:
- Total Actions Taken: {total_actions}
- Total Entities Encountered: {total_entities}
- Total Roles Encountered: {total_roles}
- Average Actions Per Round: {avg_actions_per_round:.1f}
- Action Distribution: {all_round_actions if all_round_actions else 'N/A'}
- Entity Types Encountered: {all_round_states if all_round_states else 'N/A'}
- Role Types Encountered: {all_round_roles if all_round_roles else 'N/A'}

COMPLETE MISSION CHRONOLOGY:
{chr(10).join(game_events) if game_events else 'No events recorded'}

PERFORMANCE ANALYSIS:
- {_calculate_performance_rating(humans_saved, humans_killed, zombies_saved, zombies_killed)} performance rating

Your job:
Write a SHORT, dramatic commander's report in military style. Be authoritative, use military terminology, and provide a clear assessment of the mission's success or failure. 

Focus on:
1. Overall mission success/failure
2. Key achievements or critical failures
3. Recommendations for future operations

Output format:
# [Dramatic military headline in ALL CAPS]
[Then write a 3-4 sentence commander's report in military style, around 80-100 words. Be authoritative and use military terminology.]

The report should be concise, dramatic, and provide a clear assessment of the mission's outcome.
"""

    api_key = GROQ_API_KEY
    if not api_key:
        print("[Groq] GROQ_API_KEY not set in environment.")
        return "summary unavailable"

    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
            timeout=timeout,
        )
        # Extract the summary from the response
        message = getattr(completion.choices[0], 'message', None)
        summary = getattr(message, 'content', None) if message else None
        if summary:
            summary = summary.strip()
        print(f"[Groq Final Game Summary]: {summary}")
        return summary if summary else "summary unavailable"
    except Exception as e:
        print(f"[Groq] API call for final summary failed: {e}")
        return "summary unavailable"
    
def _calculate_performance_rating(humans_saved, humans_killed, zombies_saved, zombies_killed):
    """
    Calculate performance rating based on human and zombie performance with +5 margin.
    Returns: EXCELLENT, GOOD, MEDIOCRE, POOR, or CRITICAL
    """
    human_margin = humans_saved - humans_killed
    zombie_margin = zombies_killed - zombies_saved
    
    print(f"[Performance Debug] humans_saved={humans_saved}, humans_killed={humans_killed}, zombies_saved={zombies_saved}, zombies_killed={zombies_killed}")
    print(f"[Performance Debug] human_margin={human_margin}, zombie_margin={zombie_margin}")
    
    # Both conditions satisfied with +5 margin
    if human_margin >= 5 and zombie_margin >= 5:
        print(f"[Performance Debug] → EXCELLENT")
        return "EXCELLENT"
    # Both conditions satisfied but one or both within +5 margin
    elif human_margin > 0 and zombie_margin > 0:
        print(f"[Performance Debug] → GOOD")
        return "GOOD"
    # Only one condition satisfied (human positive OR zombie positive, but not both)
    elif (human_margin > 0 and zombie_margin <= 0) or (human_margin <= 0 and zombie_margin > 0):
        print(f"[Performance Debug] → MEDIOCRE")
        return "MEDIOCRE"
    # Neither condition satisfied but some positive activity
    elif humans_saved > 0 or zombies_killed > 0:
        print(f"[Performance Debug] → POOR")
        return "POOR"
    # No positive activity at all
    else:
        print(f"[Performance Debug] → CRITICAL")
        return "CRITICAL" 