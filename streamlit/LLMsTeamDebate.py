import streamlit as st

import sys
import time
from datetime import datetime
import json
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
from pathlib import Path
from utils import Agent
from utils.Function import save_codebook_excel, save_debate_excel, import_json, save_json, zip_folder_to_bytes
from config.debate_menu import *
from config.model_menu import *


class MultiAgentsDebate:
    def __init__(self, debate_config, models_name):
        self.user_avatar = "🧑‍💻"
        self.title = "LLM Team Debate"
        self.models_name = models_name
        self.config = debate_config
        st.set_page_config(page_title=self.title, layout="wide")
        self.init_session()

    def init_session(self):
        if "chat_history" not in st.session_state:
            # introduce (F1)
            prologue = self.config["Facilitator"]["task1"]
            st.session_state.chat_history = [{
                "role": "Introduce-Prologue",
                "name": "Facilitator(Introduce)",
                "avatar": "📃",
                "content": prologue
            }]
        if "roles_identity" not in st.session_state:
            st.session_state.roles_identity = []
            st.session_state.roles_positionality = ["#########"] * 3
        if "debate_models" not in st.session_state:
            st.session_state.debate_models = self.models_name
            st.session_state.debate_responses = []
            st.session_state.closing = []
        if "agree_list" not in st.session_state:
            st.session_state.agree_list = []
        if "disagreed_list" not in st.session_state:
            st.session_state.disagreed_list = []
            st.session_state.disagreed_list_select = []
        if "Facilitator" not in st.session_state:
            st.session_state.Facilitator = None
        if "roles" not in st.session_state:
            st.session_state.roles = None

    def render_model_selectors(self):
        with st.sidebar:
            st.subheader("⚖️ LLM Team")
            st.session_state.roles_identity.clear()
            for i, role in enumerate(["Role1", "Role2", "Role3"]):
                self.render_divider()
                role_selected = st.selectbox(f"{role}", roles_Id, index=i, key=f"{role}_name")
                disciplinary_selected = st.selectbox("Disciplinary Background", Disciplinary_Background, index=i,
                                                     key=f"{role}_Disciplinary_Background")

                Area_of_Concern_selected = st.selectbox("Area of Concern", Area_of_Concern, index=i,
                                                        key=f"{role}_Area_of_Concern")

                Scope_Values_selected = st.selectbox("Scope & Values", Scope_Values, index=i,
                                                     key=f"{role}_Scope_Values")

                Methodology_selected = st.selectbox("Methodology", Methodology, index=i,
                                                    key=f"{role}_Methodology")

                Personal_Identity_Influence_selected = st.selectbox("Personal Identity Influence", Personal_Identity_Influence_selected,
                                                                    index=i,
                                                                    key=f"{role}_Personal_Identity_Influence")
                st.markdown("Positionality Statement")
                st.markdown(st.session_state.roles_positionality[i])
                st.session_state.roles_identity.append({"role": role_selected,
                                                        "Disciplinary_Background": disciplinary_selected,
                                                        "Area_of_Concern": Area_of_Concern_selected,
                                                        "Scope_Values": Scope_Values_selected,
                                                        "Methodology": Methodology_selected,
                                                        "Personal_Identity_Influence": Personal_Identity_Influence_selected,
                                                        })

    def render_sidebar_results(self):
        with st.sidebar:
            st.markdown("""
                <style>
                div.stButton > button:first-child {
                    color: red;              /* 文字颜色 */
                    padding: 10px;          /* 内边距 */
                    border-radius: 10px;       /* 圆角 */
                    font-size: 10px;         /* 字体大小 */
                    transition: 1s;        /* 平滑过渡 */
                }
                div.stButton > button:first-child:hover {
                    background-color: #45a049; /* 悬停时颜色 */
                    transform: scale(1.1);   /* 悬停放大 */
                }
                </style>
            """, unsafe_allow_html=True)

            # st.session_state.human_input = st.chat_input("Input your prompt...")

            self.render_divider()
            if st.button("Generate Positionality"):
                self.roles_stage(pos=True)
                st.markdown("Generate Finish")
            self.render_divider()

            # target_text show
            st.markdown("### Target Text")
            if st.session_state.get("target_text"):
                st.markdown(f"{st.session_state.target_text}")
            else:
                st.markdown("#########")

            self.render_divider()
            if st.button("Update WebPage/Items/Positionality"):
                pass
            self.render_divider()

            st.markdown("### ✅ Agreed Items")
            for _, item in enumerate(st.session_state.agree_list):
                st.markdown(f"- {item['code']}")

            st.markdown("---")
            st.markdown("### ⚠️ Disagreed Items")
            for idx, item in enumerate(st.session_state.disagreed_list):
                if st.button(f"🔍 {item['code']}", key=f"discuss_{idx}"):
                    st.session_state.selected_disagree = item
                    st.session_state.chat_history = [chat for chat in st.session_state.chat_history if
                                                     chat.get("role") != "Debate Agent" or chat.get(
                                                         "role") != "Debate Divider"]

    def render_user_message(self, text):
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-end; align-items: center; margin: 6px 0;'>
            <div style='background-color: #DCF8C6; padding: 10px 14px; border-radius: 10px; max-width: 70%; text-align: left;'>
                {text}
            </div>
            <div style='font-size: 24px; margin-left: 8px;'>{self.user_avatar}</div>
        </div>
        """, unsafe_allow_html=True)

    def render_agent_message(self, name, avatar, content, delay=False):
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-start; align-items: flex-start; margin: 6px 0;'>
            <div style='font-size: 24px; margin-right: 8px;'>{avatar}</div>
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
                if delay:
                    time.sleep(0.01)

        st.markdown("</div></div>", unsafe_allow_html=True)

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

    def render_chat_history(self, role, name, avatar, content):
        st.session_state.chat_history.append({
            "role": role,
            "name": name,
            "avatar": avatar,
            "content": content
        })
        self.render_agent_message(name, avatar, content, True)

    def render_chat(self):
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                self.render_user_message(msg["content"])
            elif msg["role"] in {"divider", "Debate Divider"}:
                self.render_divider(msg["content"])
            else:
                self.render_agent_message(msg["name"], msg["avatar"], msg["content"])

    def handle_input(self):
        user_input = st.chat_input("Input your target text here...")
        if user_input:
            st.session_state.target_text = user_input
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            self.render_user_message(user_input)

            st.session_state.role_reply = None
            st.session_state.agree_reply = None

            # Role_Inference_Stage
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Roles Init Codebook"
            })
            self.render_divider("Roles Init Codebook")
            self.roles_stage(st.session_state.target_text, pos=False, code_gen=True)
            self.render_chat_history("Roles Generation agent", "Role_Inference_Stage", "🔁",
                                     st.session_state.roles_annotate)
            st.session_state.role_reply = st.session_state.roles_annotate

            # Agree_Disagree_stage (F2)
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Agree/Disagree Codebook"
            })
            self.render_divider("Agree/Disagree Codebook")
            agree_disagree_reply = self.agree_disagree(user_input)
            self.render_chat_history("Agree-Disagree", "Facilitator(Agree vs Disagree)", "📃", agree_disagree_reply)
            st.session_state.agree_disagree_reply = agree_disagree_reply

            if st.session_state.role_reply and st.session_state.agree_disagree_reply:
                st.session_state.agree_list = st.session_state.agree_disagree_reply.get("Agreed", [])
                st.session_state.disagreed_list = st.session_state.agree_disagree_reply.get("Disagreed", [])
                if not st.session_state.disagreed_list:
                    save_codebook_excel("codebook.xlsx", st.session_state.target_text, st.session_state.agree_list)

            # Debate Ready (F3)
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Start Debate"
            })
            self.render_divider("Start Debate")
            st.session_state.Facilitator.event(self.config["Facilitator"]["task3"]
                                               .replace("[Target Text]", user_input)
                                               .replace("[ROLE_CODEBOOKS]", str(st.session_state.roles_annotate))
                                               .replace("[Disagreed]", str(st.session_state.disagreed_list)))
            debate_ready_reply = st.session_state.Facilitator.ask()
            st.session_state.Facilitator.memory(debate_ready_reply, False)
            self.render_chat_history("Agree-Disagree", "Facilitator(Why Disagree)", "📃", debate_ready_reply)
            st.session_state.debate_ready_reply = debate_ready_reply

    def roles_init(self):
        roles = [
            Agent.Agent(
                model_name=mdl,
                name=role,
                api_key=api_key[mdl],
                base_url=base_url[mdl]
            )
            for mdl, role in
            zip([st.session_state.debate_models[r] for r in st.session_state.debate_models],
                [r for r in st.session_state.debate_models])
        ]
        roles.pop()
        # roles system
        for role, meta in zip(roles, st.session_state.roles_identity):
            role_prompt = self.config["role_prompt"]["system"] \
                .replace("[role]", meta["role"]) \
                .replace("[Disciplinary Background]", meta["Disciplinary_Background"]) \
                .replace("[Area of Concern]", meta["Area_of_Concern"]) \
                .replace("[Scope & Values]", meta["Scope_Values"]) \
                .replace("[Methodology]", meta["Methodology"]) \
                .replace("[Personal Identity Influence]", meta["Personal_Identity_Influence"])
            role.set_meta_prompt(role_prompt)
        return roles

    def roles_stage(self, target_text="", pos=False, code_gen=False):
        # llm team (each role define)
        st.session_state.roles = self.roles_init()

        # positionality statement
        if pos:
            positionality = []
            for role in st.session_state.roles:
                role.event(self.config["role_prompt"]["positionality"])
                role_response = role.ask()
                positionality.append(role_response)
                role.memory(role_response)
            st.session_state.roles_positionality = positionality

        # roles codebook generate
        if code_gen:
            roles_annotate = []
            for role in st.session_state.roles:

                role.memory_lst.append({"role": "system", "content": f"{self.config['role_prompt']['positionality']}"})
                role.memory_lst.append({"role": "user", "content": f"{st.session_state.roles_positionality}"})

                role.event(self.config["role_prompt"]["task"].replace("[Target Text]", target_text))
                role_response = role.ask()
                role.memory(role_response)
                roles_annotate.append(
                    json.loads(role_response.replace('```', "").replace('json', '').strip()))
            st.session_state.roles_annotate = roles_annotate  # Roles Annotate list

    def agree_disagree(self, target_text):
        fac_model = st.session_state.debate_models["Facilitator"]
        Facilitator = Agent.Agent(
            model_name=fac_model,
            name="Agree_Disagree",
            api_key=api_key[fac_model],
            base_url=base_url[fac_model]
        )
        agree_agent_infer = self.config["Facilitator"]["system"]
        Facilitator.set_meta_prompt(agree_agent_infer)

        Facilitator.event(self.config["Facilitator"]["task2"]
                          .replace("[codes and justifications]", str(st.session_state.roles_annotate))
                          .replace("[Target Text]", target_text))
        view = Facilitator.ask()
        Facilitator.memory(view, False)
        st.session_state.Facilitator = Facilitator
        return json.loads(eval(view.replace('```', "'''").replace('json', '').replace('\n', '')))

    def debate_single(self, target_text, code, evidence):
        # Central Issue
        st.session_state.chat_history.append({
            "role": "divider",
            "content": "Central Issue"
        })
        self.render_divider("Central Issue")
        issue = self.config["Facilitator"]["Central Issue"]
        self.render_chat_history("Agree-Disagree", "Facilitator(Issue)", "📃", issue)

        # role system setting
        # st.session_state.roles = self.roles_init()
        meta_prompt = self.config["role_debater"]["system"].replace("[Target Text]", target_text).replace(
            "[code and justification]", str([{"code": code, "evidence": evidence}]))
        for role in st.session_state.roles:
            role.set_meta_prompt(meta_prompt)

        # role setting
        roles = []
        for j in range(len(st.session_state.roles)):
            roles.append({"name": f"{st.session_state.roles[j].name}({st.session_state.roles_identity[j]['role']})",
                          "color": color_circle[j],
                          "obj": st.session_state.roles[j]})

        # Debating
        debate_responses = []
        for i, debate in enumerate(self.config["role_debater"]["debate_round"].items()):
            st.session_state.chat_history.append({
                "role": "Debate Divider",
                "content": round_theme[i]
            })
            self.render_divider(round_theme[i])
            roles_responses = []
            for role_info in roles:
                role = role_info["obj"]
                if i == 0 or i == 3:
                    role.event(f"Round {i + 1}:\n{debate}".replace("[code]", code).replace("[code]", code))
                else:
                    role.event(f"Round {i + 1}:\n{debate}".replace("[response]", str(debate_responses[-1])))

                response = role.ask()
                response = response if f"Round {i + 1}" in response else f"Round {i + 1}\n{response}"
                roles_responses.append(f"{role_info['name']}: {response}")
                role.memory(response)
                self.render_chat_history("Debate Agent", role_info["name"], role_info["color"],
                                         response.replace(f"Round {i + 1}", ""))
            # include roles_responses of every round
            debate_responses.append(f"Round {i + 1}: {roles_responses}")

        st.session_state.debate_responses.append(debate_responses)

        # Closing (F4)
        close_prompt = self.config["Facilitator"]["task4"].replace("[debate_responses]",
                                                                   str(debate_responses))
        st.session_state.Facilitator.event(close_prompt)
        close = st.session_state.Facilitator.ask()
        st.session_state.Facilitator.memory(close, False)
        close_response = json.loads(close.replace('```', '').replace('json', '').strip())
        self.render_chat_history("Debate Agent", "Facilitator(Final Decision)", "⚖️",
                                 json.dumps(close_response, ensure_ascii=False, indent=2))
        st.session_state.closing.append(close)

        # debate finish, And process close close_response
        st.session_state.close_resolution = close_response["Resolution"]
        if close_response["Resolution"].strip().lower() == "retain":
            st.session_state.final_code = close_response["final_code"]
            st.session_state.final_justification = close_response["evidence"]

    def run(self, output_file):

        st.title(self.title)
        self.render_chat()
        self.render_model_selectors()
        self.handle_input()
        self.render_sidebar_results()

        if st.session_state.get("selected_disagree") in st.session_state.disagreed_list:
            # Single Disagreed Debate
            item = st.session_state.selected_disagree
            st.session_state.disagreed_list_select.append(item["code"])
            self.debate_single(st.session_state.target_text, item["code"], item["evidence"])
            st.session_state.disagreed_list = [i for i in st.session_state.disagreed_list if
                                               i.get("code") != item["code"]]
            resolution = st.session_state.close_resolution
            if isinstance(resolution, str) and resolution.strip().lower() != "drop":
                st.session_state.agree_list.append({"code": st.session_state.final_code,
                                                    "evidence": st.session_state.final_justification})

            if not st.session_state.disagreed_list:
                outdir = Path(f"streamlit/{output_file}").resolve()
                outdir.mkdir(parents=True, exist_ok=True)

                # Save Debate Process
                save_debate_excel(f"{outdir}/debate.xlsx", st.session_state.target_text,
                                  st.session_state.disagreed_list_select,
                                  st.session_state.debate_responses)

                # Save Final Codebook
                debate_process = []
                save_codebook_excel(f"{outdir}/codebook.xlsx", st.session_state.target_text,
                                    st.session_state.agree_list)
                for disagree, debate_responses, close_response in zip(st.session_state.disagreed_list_select,
                                                                      st.session_state.debate_responses,
                                                                      st.session_state.closing):
                    debate_process.append({
                        "Disagreed": disagree,
                        "Process": debate_responses,
                        "Closing": close_response
                    })

                result = {
                    "target_text": st.session_state.target_text,
                    "Role_Team": st.session_state.roles_identity,
                    "Role_init_codebook": st.session_state.roles_annotate,
                    "Consolidating_results": st.session_state.agree_disagree_reply,
                    "disagree_explain": st.session_state.debate_ready_reply,
                    "Debate": debate_process,
                    "Codebook": st.session_state.agree_list,
                }

                save_json(f"{outdir}/debate_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", result)

                st.markdown("### After completing all data annotation, click to package and download all the results.")

                zip_bytes = zip_folder_to_bytes(output_file)
                st.download_button(
                    label=f"Download results",
                    data=zip_bytes,
                    file_name=f"{Path(output_file).name}.zip",
                    mime="application/zip"
                )

                st.session_state.disagreed_list_select.clear()
                st.session_state.debate_responses.clear()
                st.session_state.closing.clear()


if __name__ == "__main__":
    debate_config = import_json("config/debate_config.json")

    models_name = {
        "Role1": "gpt-4o-mini",
        "Role2": "gpt-4o-mini",
        "Role3": "gpt-4o-mini",
        "Facilitator": "gpt-4o-mini",
    }
    app = MultiAgentsDebate(debate_config, models_name)
    app.run("LLMsTeamOutput")
