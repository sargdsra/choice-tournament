import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import os
from datetime import datetime

class AccumulativeTournament:
    def __init__(self, items):
        self.items = items
        self.current_winner = None
        self.comparison_history = []
        self.current_index = 0
        self.state_key = "tournament_state"
    
    def initialize_state(self):
        if self.state_key not in st.session_state:
            st.session_state[self.state_key] = {
                'current_winner': None,
                'current_index': 0,
                'comparison_history': [],
                'is_complete': False
            }
    
    def save_state(self):
        st.session_state[self.state_key] = {
            'current_winner': self.current_winner,
            'current_index': self.current_index,
            'comparison_history': self.comparison_history,
            'is_complete': self.is_complete()
        }
    
    def load_state(self):
        if self.state_key in st.session_state:
            state = st.session_state[self.state_key]
            self.current_winner = state['current_winner']
            self.current_index = state['current_index']
            self.comparison_history = state['comparison_history']
    
    def is_complete(self):
        return self.current_index >= len(self.items)
    
    def get_next_comparison(self):
        if self.is_complete():
            return None, None
        
        if self.current_index == 0:
            # First comparison: first two items
            return self.items[0], self.items[1]
        else:
            # Compare current winner with next item
            next_item = self.items[self.current_index]
            return self.current_winner, next_item
    
    def submit_choice(self, choice):
        if self.is_complete():
            return
        
        item1, item2 = self.get_next_comparison()
        
        if choice == "item1":
            winner = item1
            loser = item2
        else:
            winner = item2
            loser = item1
        
        # Record history
        self.comparison_history.append({
            'step': self.current_index + 1,
            'winner': winner['name'],
            'loser': loser['name'],
            'winner_image': winner.get('image_url', ''),
            'loser_image': loser.get('image_url', '')
        })
        
        # Update state
        self.current_winner = winner
        
        if self.current_index == 0:
            # First comparison, move to next item (index 2)
            self.current_index = 2
        else:
            # Normal case, move to next item
            self.current_index += 1
        
        self.save_state()
    
    def reset(self):
        self.current_winner = None
        self.current_index = 0
        self.comparison_history = []
        if self.state_key in st.session_state:
            del st.session_state[self.state_key]
    
    def get_final_winner(self):
        if not self.is_complete():
            return None
        return self.current_winner

def load_items_from_file(file):
    """Load items from text file with format: name,image_url"""
    items = []
    lines = file.getvalue().decode("utf-8").strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split(',')
        if len(parts) >= 1:
            name = parts[0].strip()
            image_url = parts[1].strip() if len(parts) > 1 else None
            items.append({
                'name': name,
                'image_url': image_url
            })
    
    return items

def load_sample_items():
    """Load sample items for demonstration"""
    return [
        {'name': 'Beach Vacation', 'image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=300&fit=crop'},
        {'name': 'Mountain Trek', 'image_url': 'https://images.unsplash.com/photo-1464278533981-50106e6176b1?w=400&h=300&fit=crop'},
        {'name': 'City Tour', 'image_url': 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&h=300&fit=crop'},
        {'name': 'Desert Safari', 'image_url': 'https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w-400&h=300&fit=crop'},
        {'name': 'Forest Camping', 'image_url': 'https://images.unsplash.com/photo-1504851149312-7a075b496cc7?w=400&h=300&fit=crop'},
    ]

def display_item(item, label):
    """Display an item with its image and name"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if item.get('image_url'):
            try:
                response = requests.get(item['image_url'], timeout=5)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    st.image(img, caption=label, use_container_width=True)
                else:
                    st.warning(f"Failed to load image for {item['name']}")
            except:
                st.warning(f"Could not load image for {item['name']}")
        else:
            st.info("No image available")
    
    with col2:
        st.markdown(f"### {item['name']}")
        if not item.get('image_url'):
            st.write("No image URL provided")

def main():
    st.set_page_config(
        page_title="Accumulative Choice Tournament",
        page_icon="🏆",
        layout="wide"
    )
    
    st.title("🏆 Accumulative Choice Tournament")
    st.markdown("---")
    
    # Initialize session state
    if 'tournament' not in st.session_state:
        st.session_state.tournament = None
    if 'items_loaded' not in st.session_state:
        st.session_state.items_loaded = False
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Option to load from file or use sample
        data_source = st.radio(
            "Choose data source:",
            ["Upload Text File", "Use Sample Data"]
        )
        
        items = []
        
        if data_source == "Upload Text File":
            uploaded_file = st.file_uploader(
                "Upload text file (format: name,image_url)",
                type=['txt', 'csv'],
                help="Each line should contain: Item Name,Image URL (optional)"
            )
            
            if uploaded_file:
                items = load_items_from_file(uploaded_file)
                if items:
                    st.success(f"✅ Loaded {len(items)} items from file")
                else:
                    st.error("❌ No valid items found in file")
        
        else:  # Use Sample Data
            if st.button("Load Sample Data"):
                items = load_sample_items()
                st.success(f"✅ Loaded {len(items)} sample items")
        
        # Display loaded items
        if items:
            st.subheader("📋 Loaded Items")
            for i, item in enumerate(items, 1):
                st.write(f"{i}. {item['name']}")
            
            # Start tournament button
            if st.button("🎯 Start Tournament", type="primary"):
                st.session_state.tournament = AccumulativeTournament(items)
                st.session_state.tournament.initialize_state()
                st.session_state.items_loaded = True
                st.rerun()
    
    # Main content area
    if not st.session_state.items_loaded:
        # Welcome/Instructions screen
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ## 📖 How It Works
            
            1. **Upload a text file** with your items (or use sample data)
               - Format: `Item Name,Image URL` (one per line)
               - Image URL is optional
            
            2. **Start the tournament** - items will be compared one by one
            
            3. **In each round:**
               - Keep the current winner OR choose the new option
               - The winner moves to the next round
            
            4. **Continue** until all items are compared
            
            5. **Get your final choice** with complete history
            
            ### 📝 File Format Example:
            ```
            Beach Vacation,https://example.com/beach.jpg
            Mountain Trek,https://example.com/mountain.jpg
            City Tour,https://example.com/city.jpg
            ```
            """)
        
        with col2:
            st.info("💡 **Quick Start:**\n\n1. Choose data source\n2. Load items\n3. Click 'Start Tournament'")
    
    elif st.session_state.tournament:
        tournament = st.session_state.tournament
        tournament.load_state()
        
        # Check if tournament is complete
        if tournament.is_complete():
            # Display final results
            st.balloons()
            st.success("🏁 Tournament Complete!")
            
            final_winner = tournament.get_final_winner()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("### 🏆 Final Winner")
                if final_winner:
                    display_item(final_winner, "Champion")
            
            with col2:
                st.markdown("### 📊 Comparison History")
                history_df = pd.DataFrame(tournament.comparison_history)
                if not history_df.empty:
                    # Display as table
                    display_df = history_df[['step', 'winner', 'loser']]
                    display_df.columns = ['Round', 'Winner', 'Loser']
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Option to download results
                    csv = history_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name=f"tournament_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            # Reset button
            if st.button("🔄 Start New Tournament"):
                tournament.reset()
                st.session_state.items_loaded = False
                st.session_state.tournament = None
                st.rerun()
        
        else:
            # Show current comparison
            item1, item2 = tournament.get_next_comparison()
            
            if item1 and item2:
                st.header(f"🔴 Round {tournament.current_index + 1} of {len(tournament.items)}")
                st.progress((tournament.current_index) / len(tournament.items))
                
                # Display current winner status
                if tournament.current_index > 0:
                    with st.expander("📈 Current Status", expanded=False):
                        st.info(f"**Current Champion:** {tournament.current_winner['name']}")
                        if tournament.comparison_history:
                            last_round = tournament.comparison_history[-1]
                            st.write(f"Last round: **{last_round['winner']}** vs {last_round['loser']}")
                
                # Create two columns for comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🥇 Current Winner")
                    if tournament.current_index == 0:
                        st.info("First comparison - no current winner yet")
                    display_item(item1, "Option A")
                    
                    if st.button("✅ Keep This", key="keep", type="primary", use_container_width=True):
                        tournament.submit_choice("item1")
                        st.rerun()
                
                with col2:
                    st.markdown("### 🆕 New Challenger")
                    display_item(item2, "Option B")
                    
                    if st.button("🔄 Choose This", key="choose", type="secondary", use_container_width=True):
                        tournament.submit_choice("item2")
                        st.rerun()
                
                # Add some separation
                st.markdown("---")
                
                # Show history
                if tournament.comparison_history:
                    st.subheader("📜 Comparison History")
                    
                    # Create a neat display of history
                    for entry in tournament.comparison_history:
                        col_a, col_b, col_c = st.columns([1, 2, 1])
                        with col_a:
                            st.markdown(f"**Round {entry['step']}**")
                        with col_b:
                            st.markdown(f"**{entry['winner']}** 🏅 vs {entry['loser']}")
                
                # Reset button
                if st.button("🔄 Reset Tournament", type="secondary"):
                    tournament.reset()
                    st.session_state.items_loaded = False
                    st.session_state.tournament = None
                    st.rerun()

if __name__ == "__main__":
    main()