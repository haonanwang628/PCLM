import streamlit as st
import json
import sys
import os
from LLMsTeamDebate import MultiAgentsDebate

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
from config.debate_menu import *
from utils.Function import import_json


class MultiAgentsHumanDebate(MultiAgentsDebate):
    def __init__(self, debate_config, models_name):
        super().__init__(debate_config, models_name)
        self.title = "LLM-Human Team Debate"
        st.session_state.debate_models = models_name

    def render_model_selectors(self):
        with st.sidebar:
            st.subheader("⚖️ LLM-Human Team")
            st.session_state.roles_identity.clear()
            for i, role in enumerate(["Role1", "Role2"]):
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
                Personal_Identity_Influence_selected = st.selectbox("Personal Identity Influence", Area_of_Concern,
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
            self.render_human_selectors()

    def render_human_selectors(self):
        self.render_divider()
        st.markdown("Human")

        FIELDS = [
            ("role", "Your role Identity information"),
            ("Disciplinary_Background", "Your Disciplinary Background information"),
            ("Area_of_Concern", "Your Area of Concern information"),
            ("Scope_Values", "Your Scope_Values information"),
            ("Methodology", "Your Methodology information"),
            ("Personal_Identity_Influence", "Your Personal Identity Influence information"),
        ]

        input_containers = [st.empty() for _ in FIELDS]

        values = {}
        for (k, label), container in zip(FIELDS, input_containers):
            with container:
                values[k] = st.text_input(label, key=f"human_{k}")
        if all(values.values()):
            st.session_state.roles_identity.append(values)

            for c in input_containers:
                c.empty()

            st.markdown(self.white_background_div(values["role"]), unsafe_allow_html=True)

            sections = [
                ("Disciplinary Background", values["Disciplinary_Background"]),
                ("Area of Concern", values["Area_of_Concern"]),
                ("Scope Values", values["Scope_Values"]),
                ("Methodology", values["Methodology"]),
                ("Personal Identity Influence", values["Personal_Identity_Influence"]),
            ]
            for title, content in sections:
                st.markdown(title, unsafe_allow_html=True)
                st.markdown(self.white_background_div(content), unsafe_allow_html=True)
        st.markdown("Positionality Statement")
        st.markdown(st.session_state.roles_positionality[2])

    def white_background_div(self, content):
        return f"""
        <div style="
            background-color: white;
            padding: 8px;
            border-radius: 8px;
            margin-bottom: 10px;
        ">
            {content}
        </div>
        """

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

    def debate_single(self, target_text, code, evidence):
        # ----------- Central Issue ------------
        if "debate_started" not in st.session_state:
            st.session_state.chat_history.append({
                "role": "divider",
                "content": "Central Issue"
            })
            self.render_divider("Central Issue")
            issue = self.config["Facilitator"]["Central Issue"]
            self.render_chat_history("Agree-Disagree", "Facilitator(Issue)", "📃", issue)

            # role system setting
            st.session_state.roles = self.roles_init()
            meta_prompt = self.config["role_debater"]["system"] \
                .replace("[Target Text]", target_text) \
                .replace("[code and justification]", str([{"code": code, "evidence": evidence}]))
            for role in st.session_state.roles:
                role.set_meta_prompt(meta_prompt)

            # init identity & debate vars
            st.session_state.current_round = 0
            st.session_state.current_role = 0
            st.session_state.input_finished = False
            st.session_state.setdefault("human_input", "")
            st.session_state.debate_response = []
            st.session_state.debate_started = True
            st.session_state.debate_text = ""

        # ----------- Prepare Round Info ------------
        round_keys = list(self.config["role_debater"]["debate_round"].keys())
        round_content = list(self.config["role_debater"]["debate_round"].values())
        roles = [
            {"name": f"{r.name}({st.session_state.roles_identity[i]['role']})", "color": color_circle[i], "obj": r}
            for i, r in enumerate(st.session_state.roles)
        ]

        i = st.session_state.current_round
        j = st.session_state.current_role

        # ----------- Debate in Progress ------------
        if i < len(round_keys):
            debate_key = round_keys[i]
            if not st.session_state.debate_text:
                st.session_state.debate_text = self.config["role_debater"]["debate_round"][debate_key]

            if j == 0:
                st.session_state.chat_history.append({
                    "role": "Debate Divider",
                    "content": round_theme[i]
                })
                self.render_divider(round_theme[i])
                self.render_chat_history("Introduce", "Facilitator", "📃", round_content[i])
                st.session_state[f"round_{i}_responses"] = []

            role_info = roles[j]
            role = role_info["obj"]

            # 插手人工输入
            if j == 2 and not st.session_state.input_finished:
                st.markdown(f"{role_info['color']} **{role_info['name']}** is waiting for your input:")
                st.text_input("Your Thinking", key="human_input", label_visibility="collapsed")
                if st.button("Input Finish", key=f"btn_round_{i}"):
                    st.session_state.input_finished = True
                    st.session_state.debate_text = f"{st.session_state.human_input}"
                    # human_text = f"\n\nConsider the human response carefully. " \
                    #              f"Decide whether you agree or disagree with it, and " \
                    #              f"briefly explain your reasoning. Your explanation should " \
                    #              f"be based on logical analysis, relevance to the input, and " \
                    #              f"sound judgment.\n\nHuman Response: {st.session_state.human_input}\n\n" \
                    #              f"strictly in the following output format: \n\n" \
                    #              f"**Reasoning:** briefly explain(1~3 sentence)"
                    # st.session_state.debate_text = f"{st.session_state.debate_text}{human_text}"
                    if st.button("Click here to Continue"):
                        pass

                # if st.button("Skip Input", key=f"skip_btn_round_{i}"):
                #     st.session_state.input_finished = True
                #     st.session_state.debate_text = ""
                #     if st.button("Click here to Continue"):
                #         pass

                st.stop()

            # 生成 prompt
            if i == 0 or i == 3:
                event_text = f"Round {i + 1}:\n{st.session_state.debate_text}".replace("[code]", code).replace("[code]",
                                                                                                               code)
            else:
                last_response = st.session_state.debate_response[-1] if st.session_state.debate_response else ""
                event_text = f"Round {i + 1}:\n{st.session_state.debate_text}".replace("[response]", str(last_response))

            if j != 2:
                role.event(event_text)
                response = role.ask()
                response = response if f"Round {i + 1}" in response else f"Round {i + 1}\n{response}"
                role.memory(response)
            else:
                response = st.session_state.debate_text

            self.render_chat_history("Debate Agent", role_info["name"], role_info["color"],
                                     response.replace(f"Round {i + 1}", ""))
            st.session_state[f"round_{i}_responses"].append(f"{role_info['name']}: {response}")

            # 前进一位角色
            st.session_state.current_role += 1
            if st.session_state.current_role >= len(roles):
                # 本轮结束
                st.session_state.debate_response.append(
                    f"Round {i + 1}: {st.session_state[f'round_{i}_responses']}"
                )
                del st.session_state[f'round_{i}_responses']
                st.session_state.current_round += 1
                st.session_state.current_role = 0
                st.session_state.input_finished = False
                st.session_state.debate_text = ""
                st.session_state.human_input = ""

            st.rerun()

        # ----------- Facilitator Summary ------------
        else:
            # Closing (F4)
            st.session_state.debate_responses.append(st.session_state.debate_response)
            close_prompt = self.config["Facilitator"]["task4"].replace(
                "[debate_responses]", str(st.session_state.debate_response)
            )
            st.session_state.Facilitator.event(close_prompt)
            close = st.session_state.Facilitator.ask()
            st.session_state.Facilitator.memory(close, False)
            close_response = json.loads(close.replace('```', '').replace('json', '').strip())
            self.render_chat_history("Debate Agent", "Facilitator(Final conclusion)", "⚖️",
                                     json.dumps(close_response, ensure_ascii=False, indent=2))

            # Process Final Result
            st.session_state.close_resolution = close_response["Resolution"]
            if close_response["Resolution"].strip().lower() != "drop":
                st.session_state.final_code = close_response["final_code"]
                st.session_state.final_justification = close_response["evidence"]

            # 清除起始标记，允许重复运行
            del st.session_state.debate_started


if __name__ == "__main__":
    debate_config = import_json("config/debate_config.json")
    models_name = {
        "Role1": "deepseek-chat",
        "Role2": "deepseek-chat",
        "Human": "deepseek-chat",
        "Facilitator": "deepseek-chat",
    }
    app = MultiAgentsHumanDebate(debate_config, models_name)
    app.run("LLMs-HumanOutput")
