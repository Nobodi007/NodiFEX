import json
from pathlib import Path
import streamlit as st

from services.settrade_client import connect_read_only

st.set_page_config(page_title="TFEX Terminal", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stMainBlockContainer{max-width:none!important;width:100%!important;padding-left:0!important;padding-right:0!important;padding-top:0!important}
section.main>div.block-container{max-width:none!important;width:100%!important;padding-left:0!important;padding-right:0!important;padding-top:0!important}
</style>
""", unsafe_allow_html=True)

state = connect_read_only()

# Diagnostic is rendered by Streamlit itself so it cannot be hidden by the HTML terminal.
st.markdown("### Settrade Sandbox Diagnostic")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Environment", state["environment"])
c2.metric("Broker", state["broker_id"])
c3.metric("Account", state["account"])
c4.metric("Connection", "CONNECTED" if state["connected"] else "NOT CONNECTED")

for s in state["stages"]:
    icon = "✅" if s["status"] == "OK" else ("⚠️" if s["status"] == "WARN" else "❌")
    st.write(f"{icon} **{s['name']}** — {s['status']} — {s['detail']}")

if state["errors"]:
    st.error("Settrade returned an error. See details below.")
    st.json(state["errors"])
elif state["connected"]:
    st.success("TFEX Sandbox account connected in READ-ONLY mode. No order/cancel API is called.")

html = Path(__file__).with_name("index.html").read_text(encoding="utf-8")

# Feed the real API state into the existing terminal without hard-coding demo data.
payload = json.dumps(state, ensure_ascii=False, default=str).replace("</", "<\\/")
bridge = f"""
<script>
window.__TFEX_STATE__ = {payload};
(function() {{
  const s = window.__TFEX_STATE__ || {{}};
  function money(v) {{
    if (v === null || v === undefined || v === '') return '—';
    const n = Number(v); return Number.isFinite(n) ? n.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}}) : String(v);
  }}
  function text(v) {{ return v === null || v === undefined || v === '' ? '—' : String(v); }}
  function set(id,v) {{ const e=document.getElementById(id); if(e) e.textContent=v; }}
  const banner = document.querySelector('body > div:first-child');
  if (banner) banner.innerHTML = '<b style="color:#f0f6fc">ACCOUNT MODE:</b> LIVE ACCOUNT SHELL &nbsp;•&nbsp; <span style="color:' + (s.connected ? '#27d17f' : '#f85149') + '">' + (s.connected ? 'TFEX SANDBOX CONNECTED' : 'TFEX API NOT CONNECTED') + '</span> &nbsp;•&nbsp; Read-only · No orders will be sent.';
  if (s.connected && s.account_info) {{
    const a=s.account_info;
    set('portfolio', money(a.equity ?? a.total_equity ?? a.net_asset));
    set('unreal', money(a.unrealized_pnl ?? a.unrealizedPnl));
    set('realized', money(a.realized_pnl ?? a.realizedPnl));
  }}
  const p=s.portfolio;
  if (Array.isArray(p)) {{
    const tbody=document.getElementById('positions'); if(tbody) {{
      tbody.innerHTML=''; p.forEach(x=>{{
        const tr=document.createElement('tr'); tr.innerHTML='<td class="sym">'+text(x.symbol ?? x.contract ?? x.sec_symbol)+'</td><td>'+text(x.side ?? x.position_side)+'</td><td>'+text(x.quantity ?? x.qty)+'</td><td>'+money(x.avg_price ?? x.average_price)+'</td><td>'+money(x.last_price ?? x.market_price)+'</td><td>'+money(x.unrealized_pnl ?? x.p_l)+'</td>'; tbody.appendChild(tr);
      }});
    }}
    set('posCount', p.length + ' positions');
    const no=document.getElementById('noPos'); if(no) no.style.display=p.length?'none':'block';
  }}
  const o=s.orders;
  if (Array.isArray(o)) {{
    const tbody=document.getElementById('orders'); if(tbody) {{
      tbody.innerHTML=''; o.slice(0,20).forEach(x=>{{
        const tr=document.createElement('tr'); tr.innerHTML='<td>'+text(x.order_time ?? x.timestamp ?? x.time)+'</td><td class="sym">'+text(x.symbol ?? x.contract)+'</td><td>'+text(x.side)+'</td><td>'+text(x.quantity ?? x.qty)+'</td>'; tbody.appendChild(tr);
      }});
    }}
  }}
}})();
</script>
"""

# Use the existing terminal UI, but inject live state first.
html = html.replace("</body>", bridge + "</body>")
st.components.v1.html(html, height=2400, scrolling=False)
