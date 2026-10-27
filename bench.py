"""Стенд 08f: python3 bench.py — 5 раскладов × 2 режима (войны выкл / вкл) × 500 тиков, отчёт со сверкой с нормами."""
from twin.bench import LAYOUTS, build_bench, summary


def run_layout(layout, wars_on):
    w, h = build_bench(layout, wars_on)
    for f in w.factions.values():
        w.publish_dos(f, phase=0)
    for _ in range(h):
        w.step()
    return w


def report() -> str:
    out, tot = [], dict(wars=0, goal_end=0, timeout=0, extinct=0)
    for lay in LAYOUTS:
        for on in (False, True):
            s = summary(run_layout(lay, on))
            out.append(f"расклад {lay}, войны {'вкл' if on else 'выкл'}:")
            out.append(f"   войн: {s['wars']}, тики объявлений: {s['war_ticks']}")
            out.append(f"   концы: {s['ends'] or 'нет'}; репарации выплачены раз: {s['reparations']}")
            out.append(f"   штурмов: {s['assaults']}, налётов на объекты: {s['raids']}")
            out.append(f"   потери людей по причинам: {s['losses'] or 'нет'}")
            out.append(f"   минимум запаса, сут.: {s['min_dos']}")
            out.append(f"   вымерли до конца: {s['extinct'] or 'никто'}")
            if on:
                tot["wars"] += s["wars"]
                tot["timeout"] += s["ends"].get("WAR_END_TIMEOUT", 0)
                tot["goal_end"] += s["ends"].get("WAR_END_BROKEN", 0) + s["ends"].get("WAR_END_EXHAUSTED", 0)
                tot["extinct"] += len(s["extinct"])
    out.append("")
    out.append("сводка по пяти раскладам (войны вкл):")
    out.append(f"   войн всего: {tot['wars']}; на мир в среднем {tot['wars'] / len(LAYOUTS):.1f}")
    n1 = "в норме" if 1 <= tot["wars"] / len(LAYOUTS) <= 5 else "вне нормы (норма: от 1 до 5 войн на мир за 500 суток)"
    out.append(f"   число войн на мир: {n1}")
    n2 = "в норме" if tot["goal_end"] > tot["timeout"] else ("вне нормы: нет войн" if tot["wars"] == 0 else "вне нормы (концы «сломлены»/«выдохлись» должны быть чаще «срока»)")
    out.append(f"   концы: {n2}")
    out.append(f"   вымирание от цены и репараций: {'в норме' if tot['extinct'] == 0 else 'вне нормы: вымерло фракций ' + str(tot['extinct'])}")
    return "\n".join(out)


if __name__ == "__main__":
    print(report())
