import streamlit as st
import speedtest
import json
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
from ping3 import ping
import requests
import numpy as np
from plotly.subplots import make_subplots
import threading
import socket
import platform

# Page config
st.set_page_config(
    page_title="SpeedScope - Advanced Internet Speed Analyzer",
    page_icon="🛜",
    layout="wide",
)

# Custom CSS
st.markdown("""
    <style>
        .title-text {
            font-size: 48px !important;
            font-weight: bold !important;
            color: #00b4d8 !important;
            text-align: center !important;
        }
        .subtitle-text {
            font-size: 24px !important;
            color: #90e0ef !important;
            text-align: center !important;
            margin-bottom: 30px !important;
        }
        .stProgress > div > div > div > div {
            background-color: #00b4d8 !important;
        }
        .speed-text {
            font-size: 24px !important;
            font-weight: bold !important;
            text-align: center !important;
        }
        .credit-text {
            font-size: 14px !important;
            text-align: center !important;
            color: #ff6b6b !important;
        }
        .metric-card {
            background-color: #1f1f1f !important;
            padding: 20px !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton>button {
            background-color: #00b4d8 !important;
            color: white !important;
            font-size: 18px !important;
            font-weight: bold !important;
            padding: 10px 20px !important;
            border-radius: 10px !important;
            border: none !important;
            width: 200px !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            background-color: #1f1f1f;
            padding: 20px;
            border-radius: 10px;
            margin: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Title and subtitle
st.markdown('<p class="title-text">SpeedScope</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Advanced Internet Speed Analyzer</p>', unsafe_allow_html=True)

class NetworkAnalyzer:
    def __init__(self):
        self.history_file = "speed_test_history.json"
        self.current_isp = socket.gethostbyname(socket.gethostname())
    
    def measure_jitter(self, host="8.8.8.8", samples=10):
        """Measure network jitter using ping"""
        ping_times = []
        lost_packets = 0
        
        for _ in range(samples):
            try:
                response_time = ping(host)
                if response_time is not None:
                    ping_times.append(response_time * 1000)  # Convert to ms
                else:
                    lost_packets += 1
            except Exception:
                lost_packets += 1
            time.sleep(0.1)
        
        if ping_times:
            mean_ping = np.mean(ping_times)
            jitter = np.mean([abs(ping - mean_ping) for ping in ping_times])
            packet_loss_percent = (lost_packets / samples) * 100
            return {
                'jitter': round(jitter, 2),
                'packet_loss': round(packet_loss_percent, 2),
                'mean_ping': round(mean_ping, 2)
            }
        return None

    def analyze_isp_performance(self):
        """Analyze ISP performance metrics"""
        try:
            # Get public IP and ISP info
            response = requests.get('https://ipapi.co/json/').json()
            isp_info = {
                'isp': response.get('org', 'Unknown ISP'),
                'location': f"{response.get('city', 'Unknown')}, {response.get('country_name', 'Unknown')}",
                'asn': response.get('asn', 'Unknown')
            }
            
            # Calculate metrics from history
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                df = pd.DataFrame(history)
                isp_metrics = {
                    'avg_download': round(df['download'].mean(), 2),
                    'avg_upload': round(df['upload'].mean(), 2),
                    'avg_ping': round(df['ping'].mean(), 2),
                    'consistency': round(100 - df['download'].std() / df['download'].mean() * 100, 2)
                }
            else:
                isp_metrics = None
            
            return isp_info, isp_metrics
            
        except Exception as e:
            st.error(f"Error analyzing ISP performance: {str(e)}")
            return None, None
    
    def calculate_network_health(self, metrics):
        """Calculate overall network health score"""
        if not metrics:
            return None
        
        weights = {
            'download': 0.3,
            'upload': 0.2,
            'ping': 0.15,
            'jitter': 0.15,
            'packet_loss': 0.2
        }
        
        normalized = {
            'download': min(metrics['download'] / 100, 1),
            'upload': min(metrics['upload'] / 50, 1),
            'ping': max(0, min((200 - metrics['ping']) / 200, 1)),
            'jitter': max(0, min((50 - metrics['jitter']) / 50, 1)),
            'packet_loss': max(0, min((100 - metrics['packet_loss']) / 100, 1))
        }
        
        health_score = sum(normalized[metric] * weight for metric, weight in weights.items())
        return round(health_score * 100, 2)
    
    def get_recommendations(self, metrics):
        """Generate network recommendations"""
        recommendations = []
        
        if metrics['download'] < 10:
            recommendations.append({
                'type': 'warning',
                'message': '🔸 Low download speed. Check for background downloads or network congestion.'
            })
        
        if metrics['upload'] < 5:
            recommendations.append({
                'type': 'warning',
                'message': '🔸 Low upload speed. May affect video calls and file sharing.'
            })
        
        if metrics['ping'] > 100:
            recommendations.append({
                'type': 'alert',
                'message': '🔴 High ping detected. May cause lag in online gaming and real-time apps.'
            })
        
        if metrics['packet_loss'] > 2:
            recommendations.append({
                'type': 'alert',
                'message': '🔴 Significant packet loss detected. Check network connection and cables.'
            })
        
        if metrics['jitter'] > 30:
            recommendations.append({
                'type': 'warning',
                'message': '🔸 High jitter detected. May affect streaming and video call quality.'
            })
        
        return recommendations

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'is_testing' not in st.session_state:
    st.session_state.is_testing = False
if 'current_test_data' not in st.session_state:
    st.session_state.current_test_data = None

def load_history():
    """Load test history from file"""
    if os.path.exists('speed_test_history.json'):
        with open('speed_test_history.json', 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    """Save test history to file"""
    with open('speed_test_history.json', 'w') as f:
        json.dump(history, f, indent=4)

def run_speed_test():
    """Run speed test and return results"""
    try:
        st.session_state.is_testing = True
        speed_test = speedtest.Speedtest()
        
        with st.spinner('Finding best server...'):
            speed_test.get_best_server()
        
        with st.spinner('Testing download speed...'):
            download_speed = speed_test.download() / 1_000_000
        
        with st.spinner('Testing upload speed...'):
            upload_speed = speed_test.upload() / 1_000_000
        
        ping = speed_test.results.ping
        
        # Get jitter and packet loss
        network_analyzer = NetworkAnalyzer()
        jitter_data = network_analyzer.measure_jitter()
        
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "download": round(download_speed, 2),
            "upload": round(upload_speed, 2),
            "ping": round(ping, 2),
            "jitter": jitter_data['jitter'] if jitter_data else 0,
            "packet_loss": jitter_data['packet_loss'] if jitter_data else 0
        }
        
        st.session_state.current_test_data = result
        st.session_state.history.append(result)
        save_history(st.session_state.history)
        
        return result
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None
    finally:
        st.session_state.is_testing = False

def create_speed_chart(history):
    """Create speed history chart"""
    if not history:
        return None
        
    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['download'],
        name='Download',
        line=dict(color='#00b4d8', width=3),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['upload'],
        name='Upload',
        line=dict(color='#90e0ef', width=3),
        mode='lines+markers'
    ))
    
    fig.update_layout(
        title='Speed History',
        xaxis_title='Time',
        yaxis_title='Speed (Mbps)',
        template='plotly_dark',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Load existing history
st.session_state.history = load_history()

# Create three columns for speed metrics
col1, col2, col3 = st.columns(3)

# Display current speeds
with col1:
    st.markdown('<p class="speed-text">Download Speed</p>', unsafe_allow_html=True)
    download_placeholder = st.empty()
    download_progress = st.progress(0)

with col2:
    st.markdown('<p class="speed-text">Upload Speed</p>', unsafe_allow_html=True)
    upload_placeholder = st.empty()
    upload_progress = st.progress(0)

with col3:
    st.markdown('<p class="speed-text">Ping</p>', unsafe_allow_html=True)
    ping_placeholder = st.empty()

# Center the start button
# Add this instead:
start_button = st.button(
    "Start Test",
    disabled=st.session_state.is_testing,
    use_container_width=False,
    key="start_test_button"
)

if start_button:
    result = run_speed_test()
    if result:
        # Update metrics
        download_speed = result['download']
        upload_speed = result['upload']
        ping = result['ping']
        
        download_placeholder.markdown(f'<p class="speed-text">{download_speed:.2f} Mbps</p>', unsafe_allow_html=True)
        upload_placeholder.markdown(f'<p class="speed-text">{upload_speed:.2f} Mbps</p>', unsafe_allow_html=True)
        ping_placeholder.markdown(f'<p class="speed-text">{ping:.2f} ms</p>', unsafe_allow_html=True)
        
        download_progress.progress(min(download_speed / 100, 1.0))
        upload_progress.progress(min(upload_speed / 100, 1.0))

# Display speed history chart
if st.session_state.history:
    st.plotly_chart(create_speed_chart(st.session_state.history), use_container_width=True)

# Advanced Network Analysis Tabs
st.markdown("## Advanced Network Analysis")
tab1, tab2, tab3, tab4 = st.tabs([
    "🌡️ Network Health",
    "📊 Detailed Analysis",
    "📈 Performance Trends",
    "🌐 ISP Analysis"
])

network_analyzer = NetworkAnalyzer()

with tab1:
    if st.session_state.current_test_data:
        health_score = network_analyzer.calculate_network_health(st.session_state.current_test_data)
        
        # Display health score in a gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Network Health Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#00b4d8"},
                'steps': [
                    {'range': [0, 33], 'color': "#ff6b6b"},
                    {'range': [33, 66], 'color': "#ffd93d"},
                    {'range': [66, 100], 'color': "#4dd637"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': health_score
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display recommendations
        recommendations = network_analyzer.get_recommendations(st.session_state.current_test_data)
        if recommendations:
            st.markdown("### Recommendations")
            for rec in recommendations:
                if rec['type'] == 'warning':
                    st.warning(rec['message'])
                else:
                    st.error(rec['message'])

with tab2:
    if st.session_state.current_test_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Jitter",
                f"{st.session_state.current_test_data['jitter']} ms",
                help="Lower is better. Measures the variation in ping times."
            )
            
        with col2:
            st.metric(
                "Packet Loss",
                f"{st.session_state.current_test_data['packet_loss']}%",
                help="Lower is better. Percentage of lost data packets."
            )
        
        # Create detailed metrics visualization
        if len(st.session_state.history) > 1:
            df = pd.DataFrame(st.session_state.history)
            fig = make_subplots(rows=2, cols=2)
            
            # Download speed distribution
            fig.add_trace(
                go.Histogram(x=df['download'], name="Download Speed", nbinsx=20),
                row=1, col=1
            )
            
            # Upload speed distribution
            fig.add_trace(
                go.Histogram(x=df['upload'], name="Upload Speed", nbinsx=20),
                row=1, col=2
            )
            
            # Ping over time
            fig.add_trace(
                go.Scatter(x=pd.to_datetime(df['timestamp']), y=df['ping'], 
                          name="Ping", mode='lines+markers'),
                row=2, col=1
            )
            
            # Jitter over time
            fig.add_trace(
                go.Scatter(x=pd.to_datetime(df['timestamp']), y=df['jitter'],
                          name="Jitter", mode='lines+markers'),
                row=2, col=2
            )
            
            fig.update_layout(height=600, title_text="Detailed Network Metrics")
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    if len(st.session_state.history) > 1:
        df = pd.DataFrame(st.session_state.history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate moving averages
        df['download_ma'] = df['download'].rolling(window=3).mean()
        df['upload_ma'] = df['upload'].rolling(window=3).mean()
        
        fig = go.Figure()
        
        # Add actual speeds
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['download'],
            name='Download', mode='markers',
            marker=dict(size=8, color='#00b4d8')
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['upload'],
            name='Upload', mode='markers',
            marker=dict(size=8, color='#90e0ef')
        ))
        
        # Add trend lines
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['download_ma'],
            name='Download Trend', line=dict(color='#00b4d8', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['upload_ma'],
            name='Upload Trend', line=dict(color='#90e0ef', dash='dash')
        ))
        
        fig.update_layout(
            title='Speed Trends Over Time',
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    if st.session_state.current_test_data:
        isp_info, isp_metrics = network_analyzer.analyze_isp_performance()
        
        if isp_info and isp_metrics:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ISP Information")
                st.json(isp_info)
            
            with col2:
                st.markdown("### Performance Metrics")
                st.metric("Average Download", f"{isp_metrics['avg_download']} Mbps")
                st.metric("Average Upload", f"{isp_metrics['avg_upload']} Mbps")
                st.metric("Network Consistency", f"{isp_metrics['consistency']}%")

# Credits with GitHub link
st.markdown(
    '<p class="credit-text">Made with ❤️ by <a href="https://github.com/tanishpoddar" target="_blank" style="color: #ff6b6b; text-decoration: none; border-bottom: 1px dashed #ff6b6b;">Tanish Poddar</a></p>',
    unsafe_allow_html=True)