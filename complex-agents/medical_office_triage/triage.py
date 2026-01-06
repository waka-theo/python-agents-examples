"""
---
title: Medical Office Triage System
category: complex-agents
tags: [multi_agent, agent_transfer, medical, context_preservation, chat_history]
difficulty: advanced
description: Multi-agent medical triage system with specialized departments
demonstrates:
  - Multiple specialized agents (triage, support, billing)
  - Agent-to-agent transfer with context preservation
  - Chat history truncation and management
  - Shared userdata across agent transfers
  - Room attribute updates for agent tracking
  - YAML prompt loading for agent instructions
---
"""

import logging
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta
import random

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero

from utils import load_prompt

logger = logging.getLogger("medical-office-triage")
logger.setLevel(logging.INFO)

load_dotenv()


@dataclass
class UserData:
    """Stores data and agents to be shared across the session"""
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None
    # Nouvelles données patient
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    transfer_reason: Optional[str] = None
    # Données de rendez-vous
    appointments: list = field(default_factory=list)
    # Données de facturation
    invoices: list = field(default_factory=list)

    def summarize(self) -> str:
        """Résumé du contexte pour les agents"""
        parts = []
        if self.patient_name:
            parts.append(f"Le patient s'appelle {self.patient_name}.")
        if self.transfer_reason:
            parts.append(f"Raison du transfert: {self.transfer_reason}")
        if self.appointments:
            parts.append(f"Rendez-vous enregistrés: {len(self.appointments)}")
        return " ".join(parts) if parts else ""


RunContext_T = RunContext[UserData]


class BaseAgent(Agent):
    async def on_enter(self) -> None:
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata
        try:
            if userdata.ctx and userdata.ctx.room and userdata.ctx.room.isconnected():
                await userdata.ctx.room.local_participant.set_attributes({"agent": agent_name})
        except Exception:
            pass  # Room not yet connected, skip setting attributes

        chat_ctx = self.chat_ctx.copy()

        if userdata.prev_agent:
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, keep_function_call=True
            )
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        # Ajouter le contexte patient si disponible
        context_info = userdata.summarize()
        if context_info:
            chat_ctx.add_message(
                role="system",
                content=f"Contexte: {context_info}"
            )

        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply()

    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 8,  # Augmenté pour plus de contexte
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        """Truncate the chat context to keep the last n messages."""
        def _valid_item(item) -> bool:
            if not keep_system_message and item.type == "message" and item.role == "system":
                return False
            if not keep_function_call and item.type in ["function_call", "function_call_output"]:
                return False
            return True

        new_items = []
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]

        while new_items and new_items[0].type in ["function_call", "function_call_output"]:
            new_items.pop(0)

        return new_items

    async def _transfer_to_agent(self, name: str, context: RunContext_T, reason: str = "") -> Agent:
        """Transfer to another agent while preserving context"""
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent
        userdata.transfer_reason = reason

        return next_agent


class TriageAgent(BaseAgent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions=load_prompt('triage_prompt.yaml'),
            stt=deepgram.STT(model="nova-2", language="fr"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(model="sonic-3", voice="735287ee-ce91-4b08-8de4-63315c5ba1fb", language="fr"),
            vad=vad
        )

    @function_tool
    async def save_patient_name(self, context: RunContext_T, name: str) -> str:
        """Enregistrer le nom du patient pour personnaliser la conversation.

        Args:
            name: Le prénom ou nom complet du patient
        """
        context.userdata.patient_name = name
        return f"Nom enregistré: {name}"

    @function_tool
    async def transfer_to_support(self, context: RunContext_T) -> Agent:
        """Transférer le patient au service support pour les rendez-vous et services médicaux."""
        await self.session.say("Je vous passe Sophie du service médical.")
        return await self._transfer_to_agent("support", context, "Demande de services médicaux")

    @function_tool
    async def transfer_to_billing(self, context: RunContext_T) -> Agent:
        """Transférer le patient au service facturation pour les questions d'assurance et paiement."""
        await self.session.say("Je vous passe Olivier du service facturation.")
        return await self._transfer_to_agent("billing", context, "Question de facturation")


class SupportAgent(BaseAgent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions=load_prompt('support_prompt.yaml'),
            stt=deepgram.STT(model="nova-2", language="fr"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(model="sonic-3", voice="c9115185-0086-4cf4-bfdd-0d36425db387", language="fr"),
            vad=vad
        )

    @function_tool
    async def book_appointment(
        self,
        context: RunContext_T,
        specialty: str,
        patient_reason: str
    ) -> str:
        """Prendre un rendez-vous médical pour le patient.

        Args:
            specialty: La spécialité médicale (généraliste, dermatologue, cardiologue, etc.)
            patient_reason: La raison de la consultation
        """
        # Générer des créneaux fictifs
        base_date = datetime.now() + timedelta(days=random.randint(2, 7))
        hour = random.choice([9, 10, 11, 14, 15, 16])
        appointment_date = base_date.replace(hour=hour, minute=0)

        appointment = {
            "specialty": specialty,
            "reason": patient_reason,
            "date": appointment_date.strftime("%A %d %B à %Hh%M"),
            "doctor": f"Dr. {'Martin' if specialty == 'généraliste' else 'Dupont'}"
        }
        context.userdata.appointments.append(appointment)

        patient_name = context.userdata.patient_name or "le patient"
        return f"Rendez-vous confirmé pour {patient_name} en {specialty} avec {appointment['doctor']} le {appointment['date']}. Motif: {patient_reason}"

    @function_tool
    async def check_available_slots(self, context: RunContext_T, specialty: str) -> str:
        """Vérifier les créneaux disponibles pour une spécialité.

        Args:
            specialty: La spécialité médicale recherchée
        """
        _ = context  # Utilisé pour le contexte futur
        # Générer des créneaux fictifs
        slots = []
        for _ in range(3):
            base_date = datetime.now() + timedelta(days=random.randint(2, 10))
            hour = random.choice([9, 10, 11, 14, 15, 16])
            slots.append(base_date.replace(hour=hour, minute=0).strftime("%A %d %B à %Hh%M"))

        return f"Créneaux disponibles en {specialty}: {', '.join(slots)}"

    @function_tool
    async def renew_prescription(self, context: RunContext_T, medication: str) -> str:
        """Renouveler une ordonnance pour un médicament.

        Args:
            medication: Le nom du médicament à renouveler
        """
        patient_name = context.userdata.patient_name or "Le patient"
        return f"Demande de renouvellement enregistrée pour {medication}. {patient_name} recevra l'ordonnance par email sous 24h et pourra la récupérer en pharmacie."

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        """Retransférer au triage uniquement si le patient le demande explicitement."""
        await self.session.say("Je vous repasse Léa de l'accueil.")
        return await self._transfer_to_agent("triage", context, "Retour à l'accueil")

    @function_tool
    async def transfer_to_billing(self, context: RunContext_T) -> Agent:
        """Transférer au service facturation pour les questions de paiement."""
        await self.session.say("Je vous passe Olivier du service facturation.")
        return await self._transfer_to_agent("billing", context, "Question de facturation")


class BillingAgent(BaseAgent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions=load_prompt('billing_prompt.yaml'),
            stt=deepgram.STT(model="nova-2", language="fr"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(model="sonic-3", voice="ab636c8b-9960-4fb3-bb0c-b7b655fb9745", language="fr"),
            vad=vad
        )

    @function_tool
    async def check_invoice(self, context: RunContext_T, invoice_ref: str) -> str:
        """Vérifier le statut d'une facture.

        Args:
            invoice_ref: Le numéro ou la référence de la facture
        """
        _ = context  # Utilisé pour le contexte futur
        # Simulation de facture
        amount = random.randint(25, 150)
        status = random.choice(["en attente de paiement", "payée", "en cours de remboursement"])

        return f"Facture {invoice_ref}: {amount}€ - Statut: {status}. Remboursement Sécurité Sociale: {int(amount * 0.7)}€"

    @function_tool
    async def get_payment_options(self, context: RunContext_T, amount: float) -> str:
        """Proposer des options de paiement pour un montant.

        Args:
            amount: Le montant à payer en euros
        """
        _ = context  # Utilisé pour le contexte futur
        return f"""Options de paiement pour {amount}€:
        - Paiement immédiat par carte bancaire
        - Virement bancaire (RIB envoyé par email)
        - Paiement en 3 fois sans frais: 3x {amount/3:.2f}€
        - Prélèvement automatique mensuel"""

    @function_tool
    async def check_insurance_coverage(self, context: RunContext_T, treatment: str) -> str:
        """Vérifier la couverture d'assurance pour un traitement.

        Args:
            treatment: Le type de traitement ou consultation
        """
        _ = context  # Utilisé pour le contexte futur
        coverage = random.randint(60, 100)
        return f"Couverture pour {treatment}: Sécurité Sociale {coverage}%, Mutuelle complémentaire selon votre contrat. Reste à charge estimé: {100-coverage}%"

    @function_tool
    async def setup_payment_plan(self, context: RunContext_T, total_amount: float, months: int) -> str:
        """Mettre en place un échéancier de paiement.

        Args:
            total_amount: Le montant total à échelonner
            months: Le nombre de mois souhaité
        """
        monthly = total_amount / months
        patient_name = context.userdata.patient_name or "Le patient"
        return f"Échéancier mis en place pour {patient_name}: {months} mensualités de {monthly:.2f}€. Premier prélèvement le 5 du mois prochain."

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        """Retransférer au triage uniquement si le patient le demande explicitement."""
        await self.session.say("Je vous repasse Léa de l'accueil.")
        return await self._transfer_to_agent("triage", context, "Retour à l'accueil")

    @function_tool
    async def transfer_to_support(self, context: RunContext_T) -> Agent:
        """Transférer au support pour les questions médicales."""
        await self.session.say("Je vous passe Sophie du service médical.")
        return await self._transfer_to_agent("support", context, "Question médicale")


async def entrypoint(ctx: JobContext):
    # Charger VAD une seule fois et le partager
    vad = silero.VAD.load()

    userdata = UserData(ctx=ctx)
    triage_agent = TriageAgent(vad=vad)
    support_agent = SupportAgent(vad=vad)
    billing_agent = BillingAgent(vad=vad)

    # Register all agents in the userdata
    userdata.personas.update({
        "triage": triage_agent,
        "support": support_agent,
        "billing": billing_agent
    })

    session = AgentSession[UserData](userdata=userdata)

    await session.start(
        agent=triage_agent,  # Start with the Medical Office Triage agent
        room=ctx.room,
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
