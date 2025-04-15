import gradio as gr
import requests
import random
from typing import List
from functools import lru_cache

# ------ Free APIs ------
WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"
PIXABAY_API = "https://pixabay.com/api/"
PIXABAY_KEY = "your-free-pixabay-key"  # Get one at https://pixabay.com/api/docs/

# ------ Local Recommendations Database ------
LOCAL_RECOMMENDATIONS = {
    "Paris": {
        "Food 🍜": [
            "🍽️ Breakfast: Angelina (famous hot chocolate & pastries)",
            "🥐 Lunch: Breizh Café (best crepes in Le Marais)",
            "🍷 Dinner: Bouillon Pigalle (modern French bistro)",
            "🧀 Activity: Montmartre cheese & wine tasting tour"
        ],
        "Culture 🏛️": [
            "🖼️ Morning: Louvre Museum (skip-the-line tickets)",
            "⛪ Afternoon: Sainte-Chapelle (stained glass masterpiece)",
            "🚢 Evening: Seine River cruise with Eiffel Tower views"
        ]
    },
    "Tokyo": {
        "Food 🍜": [
            "🍣 Breakfast: Tsukiji Outer Market fresh sushi",
            "🍜 Lunch: Ichiran Ramen (private booth experience)",
            "🍢 Dinner: Omoide Yokocho yakitori alley",
            "🍱 Activity: Sushi-making class in Ginza"
        ],
        "Adventure 🏔️": [
            "🎨 Morning: TeamLab Planets digital art museum",
            "🚦 Afternoon: Shibuya Crossing & Hachiko statue",
            "🍻 Evening: Golden Gai bar hopping"
        ]
    },
    "New York": {
        "Culture 🏛️": [
            "🏛️ Morning: MET Museum early access tour",
            "🚶 Afternoon: High Line elevated park walk",
            "🍕 Dinner: Joe's Pizza (best NY-style slice)"
        ]
    }
}

# ------ Photo Functions ------
def get_city_photos(city: str) -> List[str]:
    """Fetch 3 random photos of the city from Pixabay"""
    try:
        response = requests.get(
            f"{PIXABAY_API}?key={PIXABAY_KEY}&q={city}+city&orientation=horizontal&per_page=20"
        ).json()
        photos = [hit["webformatURL"] for hit in response.get("hits", [])]
        return photos[:3] if photos else [
            "https://cdn.pixabay.com/photo/2016/11/22/23/44/porsche-1851246_640.jpg",
            "https://cdn.pixabay.com/photo/2014/08/15/11/29/beach-418742_640.jpg"
        ]
    except:
        # Fallback if API fails
        return [
            "https://cdn.pixabay.com/photo/2016/11/22/23/44/porsche-1851246_640.jpg",
            "https://cdn.pixabay.com/photo/2014/08/15/11/29/beach-418742_640.jpg"
        ]

# ------ Travel Planning Functions ------
@lru_cache(maxsize=50)
def get_city_info(city: str) -> str:
    """Get city summary from Wikivoyage"""
    params = {
        "action": "query", "format": "json", "titles": city,
        "prop": "extracts", "exintro": True, "explaintext": True
    }
    try:
        response = requests.get(WIKIVOYAGE_API, params=params, timeout=5)
        page = next(iter(response.json()["query"]["pages"].values()))
        return page["extract"][:500] + "... [read more on Wikivoyage]"
    except:
        return f"{city} is a vibrant destination with rich culture and attractions."

def get_weather(city: str) -> str:
    """Free weather API"""
    try:
        return f"☁️ {requests.get(f'https://wttr.in/{city}?format=%C+%t', timeout=3).text}"
    except:
        return "⛅ Weather data unavailable"

def generate_packing_list(city: str, days: int) -> str:
    return f"""🧳 Pack for {days} days in {city}:
    - {days} outfits (mix & match)
    - {"Umbrella ☔" if "rain" in get_weather(city).lower() else "Sunglasses 🕶️"}
    - Comfortable walking shoes
    - Universal power adapter
    - Portable charger"""

def get_local_tips(city: str, interest: str) -> List[str]:
    """Get local recommendations with fallback"""
    tips = LOCAL_RECOMMENDATIONS.get(city, {}).get(interest, [])
    if not tips:
        return [
            f"Explore local {interest.lower()} spots",
            f"Visit popular {interest.lower()} locations",
            "Ask locals for hidden gems"
        ]
    return tips

def plan_trip(city: str, budget: int, days: int, interests: List[str]):
    # Budget tier
    daily_budget = budget / days
    budget_tier = "💰 Luxury" if daily_budget > 300 else "💳 Mid-range" if daily_budget > 150 else "🪙 Budget"
    
    # Generate itinerary
    itinerary = f"""# 🌍 {city} Itinerary ({days} days, ${budget})
**{get_weather(city)}**  
**Budget Style:** {budget_tier} (${daily_budget:.0f}/day)\n\n"""

    for day in range(1, days + 1):
        interest = interests[day % len(interests)]
        tips = get_local_tips(city, interest)
        
        itinerary += f"""## 🗓️ Day {day}: {interest}\n"""
        itinerary += "### 🕘 Daily Highlights\n"
        
        # Spread tips across the day
        for i, tip in enumerate(tips[:3]):  # Show max 3 tips per day
            time_slot = ["☀️ Morning", "🌇 Afternoon", "🌃 Evening"][i % 3]
            itinerary += f"- {time_slot}: {tip}\n"
        
        # Budget-specific suggestions
        itinerary += f"\n### 💡 {budget_tier} Tips\n"
        if "Luxury" in budget_tier:
            itinerary += "- Book private guided experiences\n- Reserve at Michelin-starred restaurants\n- Consider VIP passes for attractions"
        elif "Mid-range" in budget_tier:
            itinerary += "- Take small group tours\n- Try lunch specials at fine restaurants\n- Buy attraction combo tickets"
        else:
            itinerary += "- Free walking tours available\n- Street food is delicious and affordable\n- Many museums have free entry days"
        
        itinerary += "\n\n---\n"
    
    # Add practical information
    itinerary += f"""
### 📝 Travel Essentials
{generate_packing_list(city, days)}

### 🚍 Getting Around
- Best option: {'Private driver' if "Luxury" in budget_tier else 'Metro/buses'}
- Get: {'VIP airport transfers' if "Luxury" in budget_tier else 'Tourist travel pass'}
- Avoid: Rush hour (8-9:30AM, 5-7PM)

### 💰 Money Saving Tips
- Free museum days (check local calendar)
- Lunch specials at high-end restaurants
- City tourism discount cards
"""
    
    return itinerary

# ------ Gradio Interface ------
with gr.Blocks(title="✈️ Ultimate Travel Planner", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""<h1 style="text-align: center">🌎 AI Travel Genius</h1>""")
    
    with gr.Row():
        with gr.Column(scale=2):
            city = gr.Textbox(label="Destination City", value="Paris")
            budget = gr.Slider(100, 10000, value=2000, step=100, label="Total Budget ($)")
            days = gr.Dropdown([3,5,7], value=5, label="Trip Length (days)")
            interests = gr.CheckboxGroup(
                ["Food 🍜", "Culture 🏛️", "Adventure 🏔️"],
                value=["Food 🍜", "Culture 🏛️"],
                label="Your Interests"
            )
            submit = gr.Button("Generate Itinerary", variant="primary")
        
        with gr.Column(scale=3):
            output = gr.Markdown()
            with gr.Accordion("📸 City Photos", open=True):
                photo_gallery = gr.Gallery(
                    label="Destination Highlights",
                    columns=3,
                    height="auto",
                    object_fit="cover"
                )
            with gr.Accordion("🗺️ Interactive Map", open=False):
                map_html = gr.HTML()
            with gr.Accordion("🧳 Packing List", open=False):
                packing_list = gr.Markdown()

    # Examples
    gr.Examples(
        examples=[
            ["Paris", 2500, 5, ["Food 🍜", "Culture 🏛️"]],
            ["Tokyo", 3000, 7, ["Food 🍜", "Adventure 🏔️"]],
            ["New York", 3500, 4, ["Culture 🏛️"]]
        ],
        inputs=[city, budget, days, interests]
    )

    # Update all components when city changes or on submit
    def update_all(city, budget, days, interests):
        return (
            get_city_photos(city),
            f"""<iframe width="100%" height="300" src="https://maps.google.com/maps?q={city}&output=embed"></iframe>""",
            generate_packing_list(city, days),
            plan_trip(city, budget, days, interests)
        )
    
    city.change(
        fn=update_all,
        inputs=[city, budget, days, interests],
        outputs=[photo_gallery, map_html, packing_list, output]
    )
    
    submit.click(
        fn=update_all,
        inputs=[city, budget, days, interests],
        outputs=[photo_gallery, map_html, packing_list, output]
    )

if __name__ == "__main__":
    demo.launch()
