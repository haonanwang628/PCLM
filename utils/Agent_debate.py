import json
from utils.Agent import Agent
from config.model_menu import *
import random
random.seed(3)


class DebateModel:
    def __init__(self, debate_config, models_name):
        """Create a Debate Model
        Args:
            debate_config: debate prompt and debate progress design
            models_name: multi Agents(roles and Facilitator) models name,
        """
        self.config = debate_config
        self.models_name = models_name

        self.target_text = self.config["target_text"]

    def agents_init(self):
        """
            return: roles and Facilitator Agent.
        """
        roles = []
        for i, role in enumerate(self.models_name):
            roles.append(
                Agent(
                    model_name=self.models_name[role],
                    name=role,
                    api_key=api_key[self.models_name[role]],
                    base_url=base_url[self.models_name[role]]
                ))
        Facilitator = roles.pop()
        return roles, Facilitator

    def role_stage(self, roles, roles_identity):
        """
        Args:
            roles: list of all role Agent.
            roles_identity: Set up the identity for each role. [{"role":, "disciplinary_background":, "core_value":}].
        return: roles annotate----Codebook of target text.
        """
        roles_annotate, roles_positionality = [], []
        for role, meta in zip(roles, roles_identity):
            role_prompt = self.config["role_prompt"]["system"] \
                .replace("[role]", meta["role"]) \
                .replace("[Disciplinary Background]", meta["disciplinary_background"]) \
                .replace("[Core Value]", meta["core_value"])

            # roles system
            role.set_meta_prompt(role_prompt)

            # roles positionality statement
            role.event(self.config["role_prompt"]["positionality"])
            role_response = role.ask()
            roles_positionality.append(role_response)
            role.memory(role_response, False)

            # roles codebook generate
            role.event(self.config["role_prompt"]["task"].replace("[Target Text]", self.target_text))
            role_response = role.ask()
            role.memory(role_response, False)
            roles_annotate.append(
                json.loads(role_response.replace('```', "").replace('json', '').strip()))
        return roles_positionality, roles_annotate

    def agree_disagree(self, Facilitator, roles_annotate):
        """
        Args:
            Facilitator: Facilitator Agent.
            roles_annotate: roles annotate----Codebook of target text.
        return: Agreed-Disagreed Codebook and Disagreed Explain.
        """
        # Agree_Disagree_stage (F2)
        agree_agent_infer = self.config["Facilitator"]["system"]
        Facilitator.set_meta_prompt(agree_agent_infer)
        Facilitator.event(self.config["Facilitator"]["task2"]
                          .replace("[codes and justifications]", str(roles_annotate))
                          .replace("[Target Text]", self.target_text))
        view = Facilitator.ask()
        Facilitator.memory(view, False)
        agree_disagree = json.loads(eval(view.replace('```', "'''").replace('json', '').replace('\n', '')))

        # Debate Ready (F3)
        Facilitator.event(self.config["Facilitator"]["task3"]
                                               .replace("[Target Text]", self.target_text)
                                               .replace("[ROLE_CODEBOOKS]", str(roles_annotate))
                                               .replace("[Disagreed]", str(agree_disagree["Disagreed"])))
        disagree_explain = Facilitator.ask()
        Facilitator.memory(disagree_explain, False)
        return agree_disagree, disagree_explain

    def single_disagree_debate(self, roles, roles_identity, Facilitator, disagree):
        """
        Args:
            Facilitator: Facilitator Agent.
            roles: list of all role Agent.
            roles_identity: Set up the identity for each role. [{"role":, "disciplinary_background":, "core_value":}].
            disagree: disagree codebook.
        return:
        """
        meta_prompt = self.config["role_debater"]["system"].replace("[Target Text]", self.target_text).replace(
            "[code and justification]", str([{"code": disagree["code"], "evidence": disagree["evidence"]}]))
        for role, meta in zip(roles, roles_identity):
            role.memory_lst.clear()
            role_prompt = self.config["role_prompt"]["system"] \
                .replace("[role]", meta["role"]) \
                .replace("[Disciplinary Background]", meta["disciplinary_background"]) \
                .replace("[Core Value]", meta["core_value"])
            role.set_meta_prompt(role_prompt)
            role.set_meta_prompt(meta_prompt)

        roles_update = [
            {"name": f"Role1({roles_identity[0]['role']})", "obj": roles[0]},
            {"name": f"Role2({roles_identity[1]['role']})", "obj": roles[1]},
            {"name": f"Role3({roles_identity[2]['role']})", "obj": roles[2]}
        ]

        # Debating
        debate_responses = []
        for i, debate in enumerate(self.config["role_debater"]["debate_round"].items()):
            roles_responses = []
            for role_info in roles_update:
                role = role_info["obj"]
                if i > 0:
                    role.event(f"Round {i + 1}:\n{debate}".replace("[response]", str(debate_responses[-1])))
                else:
                    role.event(f"Round {i + 1}:\n{debate}")
                response = role.ask()
                response = response if f"Round {i + 1}" in response else f"Round {i + 1}\n{response}"
                roles_responses.append(f"{role_info['name']}: {response}\n\n")
                role.memory(response, False)
            # include roles_responses of every round
            debate_responses.append({f"round {i + 1}": f"{debate}",
                                     "response": f"{roles_responses}"})

        # Closing (F4)
        close_prompt = self.config["Facilitator"]["task4"] \
            .replace("[debate_responses]", str(debate_responses))
        Facilitator.event(close_prompt)
        close = Facilitator.ask()
        Facilitator.memory(close, False, False)
        close_response = json.loads(close.replace('```', '').replace('json', '').strip())

        return debate_responses, close_response
