import json

import streamlit as st

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
from utils import Agent
from utils.Function import import_json
from config.debate_menu import *
from config.model_menu import *


class SingleLLM:
    def __init__(self, model_name):
        self.title = "Single LLM (3 roles, different perspective)"
        self.model_name = model_name
        self.user_avatar = "🧑‍💻"
        self.assistant_avatar = "🤖"
        st.set_page_config(page_title=self.title, layout="wide")
        self.init_session()

    def init_session(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "roles_identity" not in st.session_state:
            st.session_state.roles_identity = []
        if "agent" not in st.session_state:
            st.session_state.agent = Agent.Agent(
                model_name=model_name,
                name="Chat",
                api_key=api_key[self.model_name],
                base_url=base_url[self.model_name],
            )
            st.session_state.agent.set_meta_prompt("You are a helpful, concise assistant.")
        if "system_prompt" not in st.session_state:
            st.session_state.system_prompt = "You are a helpful, concise assistant."

    def render_model_selectors(self):
        with st.sidebar:
            st.subheader("⚖️ LLM Team")
            st.session_state.roles_identity.clear()
            for i, role in enumerate(["Role1", "Role2", "Role3"]):
                self.render_divider()
                role_selected = st.selectbox(f"{role}", roles_Id, index=i, key=f"{role}_Id")
                Disciplinary_selected = st.selectbox("Disciplinary Background", Disciplinary_Background, index=i,
                                                     key=f"{role}_Disciplinary_Background")
                Area_selected = st.selectbox("Area of Concern", Area_of_Concern, index=i, key=f"{role}_Area_of_Concern")
                Scope_Values_selected = st.selectbox("Scope & Values", Scope_Values, index=i,
                                                     key=f"{role}_Scope_Values")
                Methodology_selected = st.selectbox("Methodology", Methodology, index=i, key=f"{role}_Methodology")
                Personal_Identity_Influence_selected = st.selectbox("Personal Identity Influence",
                                                                    Personal_Identity_Influence, index=i,
                                                                    key=f"{role}_Personal_Identity_Influence")
                st.session_state.roles_identity.append({"role": role_selected,
                                                        "Disciplinary_Background": Disciplinary_selected,
                                                        "Area_of_Concern": Area_selected,
                                                        "Scope_Values": Scope_Values_selected,
                                                        "Methodology": Methodology_selected,
                                                        "Personal_Identity_Influence": Personal_Identity_Influence_selected
                                                        })

    def render_divider(self, text=""):
        st.markdown(
            f"""
            <style>
            .custom-divider {{
                color: gray;
                text-align: center;
                border-top: 1px solid #aaa;
                padding: 10px;
                font-family: sans-serif;
            }}
            </style>
            <div class='custom-divider'>{text}</div>
            """,
            unsafe_allow_html=True
        )

    def render_user_message(self, text):
        st.markdown(f"""
         <div style='display: flex; justify-content: flex-end; align-items: center; margin: 6px 0;'>
            <div style='background-color: #DCF8C6; padding: 10px 14px; border-radius: 10px; max-width: 70%; text-align: left;'>
                {text}
            </div>
            <div style='font-size: 24px; margin-left: 8px;'>{self.user_avatar}</div>
        </div>
        """, unsafe_allow_html=True)

    def render_agent_message(self, name, content):
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-start; align-items: flex-start; margin: 6px 0;'>
            <div style='font-size: 24px; margin-right: 8px;'>{self.assistant_avatar}</div>
            <div style='background-color: #F1F0F0; padding: 10px 14px; border-radius: 10px; max-width: 75%; text-align: left;'>
            <b>{name}</b>
            </div>

        """, unsafe_allow_html=True)
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            st.json(parsed)
        except Exception:
            placeholder = st.empty()
            full = ""
            for ch in str(content):
                full += ch
                placeholder.markdown(f"<div style='font-family: monospace;'>{full}</div>", unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

    def render_chat(self):
        st.title(self.title)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                self.render_user_message(msg["content"])
            else:
                self.render_agent_message(msg["content"])

    def handle_input(self):
        user_input = st.chat_input("Input your target text here...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            self.render_user_message(user_input)
            roles_identity = []
            for meta in st.session_state.roles_identity:
                role_prompt = config["Setting_2-3"]["system"] \
                    .replace("[Role Id]", meta["role"]) \
                    .replace("[Disciplinary Background]", meta["Disciplinary_Background"]) \
                    .replace("[Area of Concern]", meta["Area_of_Concern"]) \
                    .replace("[Scope & Values]", meta["Scope_Values"]) \
                    .replace("[Methodology]", meta["Methodology"]) \
                    .replace("[Personal Identity Influence]", meta["Personal_Identity_Influence"])
                roles_identity.append(role_prompt)
            agent = st.session_state.agent
            agent.event(config["Setting_2-3"]["config"]
                        .replace("[Target Text]", user_input)
                        .replace("[Role A identity]", roles_identity[0])
                        .replace("[Role B identity]", roles_identity[1])
                        .replace("[Role C identity]", roles_identity[2]))
            reply = agent.ask()
            reply = json.loads(reply.replace('```', "").replace('json', '').strip())
            agent.memory(reply)
            self.render_agent_message("Final Codebook", reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

    def run(self):
        st.title(self.title)
        self.render_model_selectors()
        self.handle_input()


if __name__ == "__main__":
    model_name = "gpt-4o-mini"
    config = import_json("config/SingleLLM_config.json")
    app = SingleLLM(model_name)
    app.run()
