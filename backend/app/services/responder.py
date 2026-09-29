from __future__ import annotations

from typing import Any

from app.services.language_detector import LanguageCode, get_greeting, get_farewell, get_language_name


RESPONSE_TEMPLATES = {
    "en": {
        "greeting": "Hello {name}, how may I help you today?",
        "greeting_returning": "Welcome back {name}. How can I assist you?",
        "data_balance": "Your current data balance is {data} GB on {bundle}. It expires on {expiry}.",
        "bundle_activated": "Your bundle has been activated. Updated data balance: {data} GB.",
        "bundle_already_active": "Your bundle is already active. No changes needed.",
        "network_normal": "Your connection looks normal. No outage detected in your area.",
        "network_outage": "There's a service outage affecting your area. Our team is working on it.",
        "transaction": "Your last transaction was {type} for NGN {amount}, status: {status}.",
        "complaint_created": "I've logged your complaint as {ticket_id}. A specialist will review it.",
        "unknown": "I'm LiveBox AI, your telecom assistant. I didn't catch that. Could you rephrase?",
        "escalation": "I need to escalate this to a human specialist. They'll contact you shortly.",
        "farewell": "Thank you for calling LiveBox. Goodbye!",
        "proactive_offer": "By the way, you might be interested in our {offer}. Would you like to hear more?",
        "consent_required": "I'd need your consent to share offers. You can update preferences in the app.",
        "language_switch": "Sure, I can switch to {language}. How can I help?",
        "interrupted": "I was saying... {resume}",
        "barge_in": "Go ahead, I'm listening.",
        "ai_identity": "I'm LiveBox AI, your telecom assistant.",
    },
    "pid": {
        "greeting": "How far {name}, how I fit help you today?",
        "greeting_returning": "Welcome back {name}. Wetin you want make I do for you?",
        "data_balance": "Your data balance na {data} GB for {bundle}. E go expire for {expiry}.",
        "bundle_activated": "Your bundle don activate. New data balance: {data} GB.",
        "bundle_already_active": "Your bundle dey active already. No change.",
        "network_normal": "Network dey okay. No outage for your area.",
        "network_outage": "Network don cut for your area. We dey work on am.",
        "transaction": "Your last transaction na {type} for NGN {amount}, status: {status}.",
        "complaint_created": "I don write your complaint as {ticket_id}. Person go check am.",
        "unknown": "I be LiveBox AI, your telecom assistant. I no hear you well. Talk am again?",
        "escalation": "I go carry this give human person. Dem go call you.",
        "farewell": "Tank you for calling LiveBox. Bye bye!",
        "proactive_offer": "By the way, you fit like our {offer}. You wan hear more?",
        "consent_required": "I need your permission to share offers. You fit change am for app.",
        "language_switch": "No wahala, I fit switch to {language}. How I fit help?",
        "interrupted": "I bin dey talk... {resume}",
        "barge_in": "Talk, I dey hear.",
        "ai_identity": "I be LiveBox AI, your telecom assistant.",
    },
    "yo": {
        "greeting": "Bawo ni {name}, bawo ni mo le ran ọ lọwọ?",
        "greeting_returning": "Kaabo pada {name}. Kilo mo le se fun ẹ?",
        "data_balance": "Dara ẹ ti data wa {data} GB lori {bundle}. A yoo padabo ni {expiry}.",
        "bundle_activated": "Bundle rẹ ti wa. Dara ẹ tuntun: {data} GB.",
        "bundle_already_active": "Bundle rẹ wa nikan. Ko si iyanu.",
        "network_normal": "Network dara. Ko si iroju nibo ti o wa.",
        "network_outage": "Network ti padabo nibo ti o wa. Awa nṣe iranṣẹ lori.",
        "transaction": "Iṣowo ẹ ti kọja jẹ {type} fun NGN {amount}, ipo: {status}.",
        "complaint_created": "Mo ti kọ fẹkunnu rẹ sí {ticket_id}. Oluranlọwọ yoo rii.",
        "unknown": "Emi ni LiveBox AI, oluranlọwọ ẹ ti telecom. Mi ko ye ẹ daradara. Ṣe afikun?",
        "escalation": "Mo yoo fi ẹ han fun eniyan ti a le ri. Wọn yoo pe ẹ.",
        "farewell": "E dupe fun kira LiveBox. Ɔdàbọ!",
        "proactive_offer": "Nitorina, ẹ le fẹ iranṣẹ wa {offer}.  Ṣe o fẹ kọ ẹ si?",
        "consent_required": "Mo nílòye rẹ lati fi iranṣẹ han.  Ṣe le ṣe ẹ lórí àpẹrẹ.",
        "language_switch": "Bẹẹni, mo le tọka sí {language}. Bawo ni mo le ran ọ?",
        "interrupted": "Mo ti nṣọ... {resume}",
        "barge_in": "Ṣọrọ, mo nṣọwọ.",
        "ai_identity": "Emi ni LiveBox AI, oluranlọwọ ẹ ti telecom.",
    },
    "ha": {
        "greeting": "Sannu {name}, yaya zan iya taimake ka?",
        "greeting_returning": "Barka da dawo {name}. Yaya zan iya taimake?",
        "data_balance": "Dawan data na {data} GB kan {bundle}. Zai kwace ran {expiry}.",
        "bundle_activated": "Bundle ya fara. Sabon dawan data: {data} GB.",
        "bundle_already_active": "Bundle ya fara kala. Ba wani gyara.",
        "network_normal": "Network daidai. Babu kuskure a wurinka.",
        "network_outage": "Kuskuren network a wurinka. Mun ajiye shi a kan gaba.",
        "transaction": "Iya da ta karshe ta {type} na NGN {amount}, matsayi: {status}.",
        "complaint_created": "Na rubuta gaggawa na {ticket_id}. Mai aiki zai duba.",
        "unknown": "Ni LiveBox AI, mai taimakon telecom. Ban gane ba. Za ka sake magana?",
        "escalation": "Zan haɗa da mutum. Zai kira ka.",
        "farewell": "Na gode da kira LiveBox. Sai anjima!",
        "proactive_offer": "Kuma, ka iya soyi {offer}. Ka so ka ji karin bayani?",
        "consent_required": "Ina buƙatar idonka don haɗa wa da kawance. Za ka iya gyara a app.",
        "language_switch": "Eh, zan iya canza zuwa {language}. Yaya zan taimake?",
        "interrupted": "Na fada... {resume}",
        "barge_in": "Magana, ina sauraron ka.",
        "ai_identity": "Ni LiveBox AI, mai taimakon telecom.",
    },
    "ig": {
        "greeting": "Nnoọ {name}, kedu ka m ga-enyere gị aka?",
        "greeting_returning": "Nnoọ ọzọ {name}. Kedu ka m ga-esi enyere gị aka?",
        "data_balance": "Akara data gị bụ {data} GB na {bundle}. Ga-epụta n' {expiry}.",
        "bundle_activated": "Bundle gị ekepụtara. Akara data ọhụrụ: {data} GB.",
        "bundle_already_active": "Bundle gị dị nke ọma. Enweghị ihe ọzọ.",
        "network_normal": "Network dị mma. Enweghị nsogbu n'ebe gị.",
        "network_outage": "Enwe nsogbu network n'ebe gị. Anyị na-achọsọ ya.",
        "transaction": "Ntinyeego gị bụ {type} n'ego NGN {amount}, nhazi: {status}.",
        "complaint_created": "Mere m njikwa gị ka {ticket_id}. Onye ọrụ ga-azụta ya.",
        "unknown": "A bụ m LiveBox AI, onye enyere aka telecom. Achọghị m ịhụ gị nke ọma. Gwazie gị?",
        "escalation": "Ga-amalite onye ọzọ. Ọ ga-akpọ gị.",
        "farewell": "Daalụ maka kpọrọ LiveBox. Ka ọ dị!",
        "proactive_offer": "Maka naabọ, ị chọrọ ịma ka {offer}. Ị chọrọ ịnweta ozọ?",
        "consent_required": "Achọrọ m ikike gị ịkawa ngwa. Ị ga-esi mee ya n'app.",
        "language_switch": "Ee, m ga-eso ije na {language}. Kedu ka m ga-esi enyere gị aka?",
        "interrupted": "M na-agwa... {resume}",
        "barge_in": "Kwuo, m na-enyere nti.",
        "ai_identity": "A bụ m LiveBox AI, onye enyere aka telecom.",
    },
}


def get_template(language: LanguageCode, key: str) -> str:
    templates = RESPONSE_TEMPLATES.get(language, RESPONSE_TEMPLATES["en"])
    return templates.get(key, RESPONSE_TEMPLATES["en"].get(key, ""))


def format_response(language: LanguageCode, key: str, **kwargs) -> str:
    template = get_template(language, key)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def generate_greeting(name: str, language: LanguageCode, is_returning: bool = False) -> str:
    key = "greeting_returning" if is_returning else "greeting"
    return format_response(language, key, name=name)


def generate_farewell(language: LanguageCode) -> str:
    return get_farewell(language)


def generate_ai_identity(language: LanguageCode) -> str:
    return format_response(language, "ai_identity")


def generate_data_balance_response(data: float, bundle: str, expiry: str, language: LanguageCode) -> str:
    return format_response(language, "data_balance", data=data, bundle=bundle, expiry=expiry)


def generate_bundle_response(message: str, data: float, language: LanguageCode) -> str:
    if "completed" in message.lower() or "activated" in message.lower():
        return format_response(language, "bundle_activated", data=data)
    return format_response(language, "bundle_already_active")


def generate_network_response(status: str, message: str, language: LanguageCode) -> str:
    if status == "outage_detected":
        return format_response(language, "network_outage")
    return format_response(language, "network_normal")


def generate_transaction_response(trans_type: str, amount: int, status: str, language: LanguageCode) -> str:
    return format_response(language, "transaction", type=trans_type, amount=f"{amount:,}", status=status)


def generate_complaint_response(ticket_id: str, language: LanguageCode) -> str:
    return format_response(language, "complaint_created", ticket_id=ticket_id)


def generate_unknown_response(language: LanguageCode) -> str:
    return format_response(language, "unknown")


def generate_escalation_response(language: LanguageCode) -> str:
    return format_response(language, "escalation")


def generate_proactive_offer(offer: str, language: LanguageCode) -> str:
    return format_response(language, "proactive_offer", offer=offer)


def generate_consent_required(language: LanguageCode) -> str:
    return format_response(language, "consent_required")


def generate_language_switch(language: LanguageCode, target_language: str) -> str:
    return format_response(language, "language_switch", language=target_language)


def generate_interrupted_response(resume_text: str, language: LanguageCode) -> str:
    return format_response(language, "interrupted", resume=resume_text)


def generate_barge_in_response(language: LanguageCode) -> str:
    return format_response(language, "barge_in")


def build_spoken_response(
    language: LanguageCode,
    intent: str,
    tool_result: dict | None,
    customer_name: str,
    is_first_message: bool = False,
    proactive_offer: str | None = None,
) -> str:
    parts = []
    
    if is_first_message or intent == "greeting":
        parts.append(generate_greeting(customer_name, language, is_returning=not is_first_message))
        parts.append(generate_ai_identity(language))
    
    if intent == "data_balance" and tool_result:
        result = tool_result.get("result", {})
        parts.append(generate_data_balance_response(
            result.get("data", 0),
            result.get("bundle", ""),
            result.get("expiry", ""),
            language,
        ))
    elif intent == "bundle_issue" and tool_result:
        result = tool_result.get("result", {})
        parts.append(generate_bundle_response(
            result.get("message", ""),
            result.get("updated_data", 0),
            language,
        ))
    elif intent == "network" and tool_result:
        result = tool_result.get("result", {})
        parts.append(generate_network_response(
            result.get("status", ""),
            result.get("message", ""),
            language,
        ))
    elif intent == "transaction" and tool_result:
        result = tool_result.get("result", {})
        parts.append(generate_transaction_response(
            result.get("type", ""),
            result.get("amount", 0),
            result.get("status", ""),
            language,
        ))
    elif intent == "complaint" and tool_result:
        result = tool_result.get("result", {})
        parts.append(generate_complaint_response(result.get("id", ""), language))
    elif intent == "unknown":
        parts.append(generate_unknown_response(language))
    elif intent == "escalation":
        parts.append(generate_escalation_response(language))
    
    if proactive_offer and tool_result and tool_result.get("ok"):
        parts.append(proactive_offer)
    
    response = " ".join(parts)
    
    if len(response) > 300:
        sentences = response.split(". ")
        response = ". ".join(sentences[:3])
        if not response.endswith("."):
            response += "."
    
    return response