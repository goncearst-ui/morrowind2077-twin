"""Задача 01: личное состояние именных и чистые функции по трейтам (spec 01). Рядовые состояния не имеют."""

TRAITS = ("Neuroticism_High", "Neuroticism_Low", "Agreeableness_Low", "Agreeableness_High", "Conscientiousness_High", "Openness_High")


def temperament(traits, swap34=False) -> str | None:
    """Ярлык темперамента: первая подходящая строка [док 01]. Ничего не хранится."""
    t = set(traits)
    nh, nl, al, ch, oh = "Neuroticism_High" in t, "Neuroticism_Low" in t, "Agreeableness_Low" in t, "Conscientiousness_High" in t, "Openness_High" in t
    rows = [(nh and al, "Вспыльчивый"), (nh, "Пугливый"), (nl and al, "Хладнокровный"), (nl and ch, "Упёртый"), (oh, "Бродяга")]
    if swap34:   # только для обратной проверки R84
        rows[2], rows[3] = rows[3], rows[2]
    for cond, name in rows:
        if cond:
            return name
    return None


def bucket_of(traits, steady_for_skittish=False) -> str:
    """Ведро по трейтам [док 03]."""
    t = set(traits)
    if "Neuroticism_High" in t and not steady_for_skittish:
        return "skittish"
    if "Neuroticism_Low" in t and "Conscientiousness_High" in t:
        return "steady"
    return "ordinary"


def package_for(archetype, role_kw, traits, fear=None, loyalty=None, share_dropped=False, night=False, avoid_fear=70, disaffected_loyalty=30) -> str:
    """Стек пакетов, первая подходящая строка [док 01]. fear и loyalty заданы только у именных."""
    t = set(traits)
    if fear is not None and fear >= avoid_fear:
        return "Avoid_Package"
    if loyalty is not None and loyalty < disaffected_loyalty and share_dropped:
        return "Disaffected_Pkg"
    if archetype == "Хищники" and role_kw == "Role_Soldier" and "Neuroticism_Low" in t:
        return "Raid_Package"
    if archetype == "Хищники" and "Neuroticism_High" in t:
        return "Loot_Avoid_Pkg"
    if archetype == "Контролёры" and role_kw == "Role_Soldier":
        return "Toll_Package"
    return "Home_Sandbox" if night else "Work_Sandbox"
