import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import timedelta

# --- 0. 页面配置与深色 CSS ---
st.set_page_config(
    page_title= "HappyFruit!",
    page_icon="🍒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { 
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif; 
        background-color: #0E1117; 
        color: #E0E0E0;
    }
    
    h1 { color: #FF80AB !important; font-weight: 600; letter-spacing: 1px; margin-bottom: 20px;}
    
    .chart-title {
        color: #B0BEC5;
        font-size: 1.1em;
        font-weight: 500;
        margin-top: 20px;
        margin-bottom: 5px;
        padding-left: 5px;
        border-left: 3px solid #FF80AB;
        line-height: 1.2;
    }
    
    .kpi-container {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 30px;
    }
    .kpi-card {
        background-color: #1A1C24;
        border: 1px solid #30333F;
        border-radius: 8px;
        padding: 15px 20px;
        flex: 1;
        min-width: 150px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .kpi-label { font-size: 0.8em; color: #757575; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-value { font-size: 1.6em; font-weight: 700; color: #F5F5F5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    
    .thought-card {
        background-color: #1A1C24;
        border-left: 3px solid #FF80AB;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 12px;
        border-top: 1px solid #30333F;
        border-right: 1px solid #30333F;
        border-bottom: 1px solid #30333F;
    }
    .thought-content { font-size: 0.95em; color: #E0E0E0; line-height: 1.5; margin-bottom: 8px; }
    .thought-meta { display: flex; justify-content: space-between; font-size: 0.8em; color: #616161; }
    
    .tag { padding: 1px 5px; border-radius: 3px; margin-right: 4px; font-size: 0.8em; border: 1px solid transparent;}
    .tag-dom { background: #1A237E; color: #9FA8DA; border-color: #3949AB; }
    .tag-cat { background: #004D40; color: #80CBC4; border-color: #00897B; }
    
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 1. 数据加载 ---
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(current_dir), "data", "parsed_logs.jsonl")
    if not os.path.exists(data_path): return pd.DataFrame()

    data = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            try: data.append(json.loads(line))
            except: continue
    
    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    for c in ['category', 'action', 'domain', 'reference', 'thoughts']:
        if c in df.columns: df[c] = df[c].fillna("")
    return df

# --- 2. 数据处理 ---
def aggregate_entries(df):
    if df.empty: return pd.DataFrame()
    def agg_set(x): return list(set([i for i in x if i]))
    def agg_first(x): return next((i for i in x if i), "")
    return df.groupby('timestamp').agg({
        'category': agg_set, 'domain': agg_set, 'action': agg_first, 'thoughts': agg_first
    }).reset_index()

def get_kpi_data(df, df_agg):
    total = len(df_agg)
    days = df['date'].nunique()
    
    exploded_dom = df_agg.explode('domain')
    top_dom = "-"
    if not exploded_dom.empty:
        v = exploded_dom[exploded_dom['domain']!=""]
        if not v.empty: top_dom = v['domain'].value_counts().idxmax()
        
    all_act = pd.concat([df['category'], df['action']])
    all_act = all_act[all_act!=""]
    top_act = all_act.value_counts().idxmax() if not all_act.empty else "-"
    return total, days, top_dom, top_act

# --- 3. 核心绘图逻辑 ---

def generate_perfect_heatmap(df, col_name, color_scale='Blues'):
    if df.empty: return None, 0

    df_clean = df[df[col_name] != ""].copy()
    if df_clean.empty: return None, 0

    # 1. 确定粒度 (使用日历日期计算)
    min_date = df['timestamp'].dt.date.min()
    max_date = df['timestamp'].dt.date.max()
    
    # 计算日历天数差 (包含首尾)
    days_span = (max_date - min_date).days + 1
    
    if days_span > 196:
        freq = 'M'
        date_unit_text = "/每月"
        full_range = pd.period_range(start=min_date, end=max_date, freq='M')
        df_clean['period'] = df_clean['timestamp'].dt.to_period('M')
        start_label = str(full_range[0])
        end_label = str(full_range[-1])
    elif days_span > 112:
        freq = 'W-MON'
        date_unit_text = "/每周"
        full_range = pd.period_range(start=min_date, end=max_date, freq='W-MON')
        df_clean['period'] = df_clean['timestamp'].dt.to_period('W-MON')
        start_label = str(full_range[0]).split('/')[0]
        end_label = str(full_range[-1]).split('/')[0]
    elif days_span > 56:
        freq = "4D"
        date_unit_text = "/每四日"
        df_clean['period'] = df_clean['timestamp'].dt.floor('4D').dt.strftime('%Y-%m-%d')
        freq_range = pd.date_range(start=min_date, end=max_date, freq='4D')
        full_range = [d.strftime('%Y-%m-%d') for d in freq_range]
        start_label = full_range[0]
        end_label = full_range[-1]
    elif days_span > 28:
        freq = "2D"
        date_unit_text = "/每两日"
        df_clean['period'] = df_clean['timestamp'].dt.floor('2D').dt.strftime('%Y-%m-%d')
        # 生成骨架，从最小日期到最大日期的连续时间点，步长为2天
        freq_range = pd.date_range(start=min_date, end=max_date, freq='2D')
        # 转成字符串列表 (这是关键，必须和 period 列的格式一致)
        full_range = [d.strftime('%Y-%m-%d') for d in freq_range]
        # 3. 确定首尾标签
        start_label = full_range[0]
        end_label = full_range[-1]
    else:
        freq = 'D'
        date_unit_text = "/每日"
        full_range = pd.period_range(start=min_date, end=max_date, freq='D')
        df_clean['period'] = df_clean['timestamp'].dt.to_period('D')
        start_label = full_range[0].strftime("%m-%d")
        end_label = full_range[-1].strftime("%m-%d")

    # 2. 统计
    counts = df_clean.groupby(['period', col_name]).size().reset_index(name='count')
    matrix = counts.pivot(index=col_name, columns='period', values='count').fillna(0)
    matrix = matrix.reindex(columns=full_range, fill_value=0)
    
    total_counts = matrix.sum(axis=1).sort_values(ascending=True)
    matrix = matrix.loc[total_counts.index]
    
    z_data = matrix.values
    y_labels = matrix.index.tolist()
    nx = len(matrix.columns)
    ny = len(y_labels)
    
    # 3. 尺寸
    CELL_SIZE = 20
    GAP = 3
    plot_height_pixels = ny * (CELL_SIZE + GAP)
    
    MARGIN_T = 30
    MARGIN_B = 80
    MARGIN_L = 10
    MARGIN_R = 150
    total_height = plot_height_pixels + MARGIN_T + MARGIN_B
    total_width = 800 
    
    # 4. 绘图
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=z_data,
        x=list(range(nx)),
        y=y_labels,
        colorscale=color_scale,
        showscale=True,
        colorbar=dict(
            orientation='h',
            y=1.0, 
            x=1.0, 
            yanchor='bottom',
            xanchor='right',
            len=0.2,
            thickness=6,
            tickfont=dict(color='#757575', size=9),
            title=dict(text="", side="right")
        ),
        xgap=GAP,
        ygap=GAP,
    ))
    
    # 5. 布局
    fig.update_layout(
        width=total_width,
        height=total_height,
        margin=dict(l=MARGIN_L, r=MARGIN_R, t=MARGIN_T, b=MARGIN_B),
        paper_bgcolor='#262730',
        plot_bgcolor='rgba(0,0,0,0)',
        
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-0.5, 35],
            scaleanchor="y",
            scaleratio=1,
            fixedrange=True
        ),
        
        yaxis=dict(
            side='right',
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=12, color="#B0BEC5"),
            ticklen=8,
            tickcolor="#455A64",
            fixedrange=True
        ),
        
        # 修正后的 annotations (删除了 ysizemode)
        annotations=[
            dict(
                x=0, y=0, xref="x", yref="paper", yshift=-15, # <--- 修正
                text=f"起：{start_label} ~",
                showarrow=False, xanchor="left", yanchor="top",
                font=dict(color="#90A4AE", size=11)
            ),
            dict(
                x=max(nx-1, 6.5), y=0, xref="x", yref="paper", yshift=-15, # <--- 修正
                text=f"止：{end_label} {date_unit_text}",
                showarrow=False, xanchor="right", yanchor="top",
                font=dict(color="#90A4AE", size=11)
            )
        ]
    )
    
    return fig, total_height

def generate_vitality_line(df_agg):
    if df_agg.empty: return None
    
    daily = df_agg.groupby(df_agg['timestamp'].dt.date).size().reset_index(name='count')
    min_d, max_d = daily['timestamp'].min(), daily['timestamp'].max()
    # plot_min = min_d - timedelta(days=1)
    # plot_max = max_d + timedelta(days=1)
    plot_min, plot_max = min_d, max_d
    
    idx = pd.date_range(min_d, max_d)
    daily.set_index('timestamp', inplace=True)
    daily = daily.reindex(idx, fill_value=0).reset_index()
    daily.columns = ['date', 'count']
    
    fig = go.Figure(go.Scatter(
        x=daily['date'], y=daily['count'],
        mode='lines',
        fill='tozeroy',
        line=dict(color='#FF80AB', width=2),
        fillcolor='rgba(255, 128, 171, 0.1)'
    ))
    
    start_str = "起："+ min_d.strftime("%m-%d") + "~"
    end_str = "止："+ max_d.strftime("%m-%d") + " /每日"

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=60, t=20, b=60),
        paper_bgcolor='#31333F',
        plot_bgcolor='rgba(0,0,0,0)',
        
        xaxis=dict(
            showticklabels=False, 
            showgrid=False,
            zeroline=False,
            range=[plot_min, plot_max],
            ticks="outside",
            ticklen=5,
            tickcolor="#546E7A"
        ),
        
        yaxis=dict(
            showgrid=True,
            gridcolor="#30333F",
            tickfont=dict(color="#607D8B", size=10),
            title=dict(
                text="条目统计", 
                font=dict(size=10, color="#90A4AE"),
                standoff=10
            )
        ),
        
        # 修正后的 annotations (删除了 ysizemode)
        annotations=[
             dict(
                x=0, y=0, xref="paper", yref="paper", yshift=-20, # <--- 修正
                text=start_str, 
                showarrow=False, xanchor="left", yanchor="top",
                font=dict(color="#90A4AE", size=11)
            ),
            dict(
                x=1, y=0, xref="paper", yref="paper", yshift=-20, # <--- 修正
                text=end_str,
                showarrow=False, xanchor="right", yanchor="top",
                font=dict(color="#90A4AE", size=11)
            )
        ]
    )
    return fig

# --- 主程序 ---
def main():
    if 'focus_time' not in st.session_state: st.session_state.focus_time = None
    df_raw = load_data()
    
    c1, c2 = st.columns([2, 1])
    with c1: st.title("🍒 YourHappyFruit!")
    with c2:
        if not df_raw.empty:
            st.markdown("###### 📅 选择时间范围", unsafe_allow_html=True)
            min_d, max_d = df_raw['date'].min(), df_raw['date'].max()
            def_start = max(min_d, max_d - timedelta(days=30))
            dates = st.date_input("📅", (def_start, max_d), label_visibility="collapsed")
            if len(dates)==2: df = df_raw[(df_raw['date']>=dates[0])&(df_raw['date']<=dates[1])] #如果 dates 有选择，按照选择过滤数据
            else: df = df_raw
        else:
            df = pd.DataFrame()

    st.markdown("---")
    main_col, side_col = st.columns([3, 1], gap="large")

    with side_col:
        st.markdown('<div class="chart-title">📝 碎碎念时间轴</div>', unsafe_allow_html=True)
        if not df.empty:
            df_agg = aggregate_entries(df)
            timeline = df_agg.sort_values('timestamp', ascending=False).head(20)
            for _, row in timeline.iterrows():
                content = row['thoughts'] if row['thoughts'] else "*(无内容)*"
                ts = row['timestamp'].strftime("%m-%d %H:%M")
                tags = ""
                for c in row['category']: tags += f'<span class="tag tag-cat">#{c}</span>'
                for d in row['domain']: tags += f'<span class="tag tag-dom">@{d}</span>'
                st.markdown(f"""
                <div class="thought-card">
                    <div class="thought-content">{content}</div>
                    <div class="thought-meta"><div>{tags}</div><div>{ts}</div></div>
                </div>""", unsafe_allow_html=True)

    with main_col:
        if not df.empty:
            df_agg_full = aggregate_entries(df)
            total, days, top_d, top_act = get_kpi_data(df, df_agg_full)
            
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-card"><div class="kpi-label">累计记录</div><div class="kpi-value">{total}</div></div>
                <div class="kpi-card"><div class="kpi-label">活跃天数</div><div class="kpi-value">{days}</div></div>
                <div class="kpi-card kpi-card-wide" title="{top_d}"><div class="kpi-label">最近专注领域</div><div class="kpi-value">{top_d}</div></div>
                <div class="kpi-card kpi-card-wide" title="{top_act}"><div class="kpi-label">最近主要活动</div><div class="kpi-value">{top_act}</div></div>
            </div>
            """, unsafe_allow_html=True)
            
            fig_dom, h_dom = generate_perfect_heatmap(df, 'domain', 'Blues')
            if fig_dom: 
                st.markdown("#### 🌌 最近关注领域", unsafe_allow_html=True)
                # st.plotly_chart(fig_dom, width='stretch', height=h_dom)
                st.plotly_chart(fig_dom, width='stretch', height=h_dom, theme=None)

            fig_act, h_act = generate_perfect_heatmap(df, 'action', 'Oranges')
            if fig_act: 
                st.markdown('#### 🔨 最近活动', unsafe_allow_html=True)
                st.plotly_chart(fig_act, width='stretch', height=h_act)

            fig_cat, h_cat = generate_perfect_heatmap(df, 'category', 'Greens')
            if fig_cat: 
                st.markdown('#### 🌳 最近忙于', unsafe_allow_html=True)
                st.plotly_chart(fig_cat, width='stretch', height=h_cat)

            fig_line = generate_vitality_line(df_agg_full)
            if fig_line: 
                st.markdown('#### 📈 每日活力', unsafe_allow_html=True)
                st.plotly_chart(fig_line, width='stretch')

        else:
            st.info("No Data yet.")

if __name__ == "__main__":
    main()