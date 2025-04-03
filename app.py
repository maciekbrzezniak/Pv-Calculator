import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Kalkulator Fotowoltaiki", layout="wide")


# ===================================================
# Pomocnicza funkcja do symulacji autokonsumpcji z magazynem
# ===================================================
def symulacja_autokonsumpcji_z_baterią(roczne_zuzycie, roczna_produkcja, cena_pradu,
                                       pojemnosc_magazynu, sprawnosc_magazynu, koszt_magazynowania=0.2):
    """
    Zaawansowana symulacja autokonsumpcji z baterią.
    Uwzględnia zmienność produkcji i zużycia w skali roku oraz opłacalność poboru energii z magazynu vs. sieci.
    """

    # Zmienność produkcji i zużycia (sezonowość)
    daily_usage = np.random.normal(roczne_zuzycie / 365.0, roczne_zuzycie * 0.1 / 365.0, 365)
    daily_prod = np.random.normal(roczna_produkcja / 365.0, roczna_produkcja * 0.2 / 365.0, 365)

    stan_baterii = 0.0
    max_batt = pojemnosc_magazynu
    eff = sprawnosc_magazynu

    total_self_consumption = 0.0
    total_from_network = 0.0
    total_from_battery = 0.0

    for usage, prod in zip(daily_usage, daily_prod):
        # Pokrycie bieżącego zużycia z produkcji
        used_direct = min(prod, usage)
        leftover = prod - used_direct
        usage_remain = usage - used_direct

        # Ładowanie magazynu z nadwyżki tylko wtedy, gdy się to opłaca
        if leftover > 0:
            can_store = max_batt - stan_baterii  # ile można jeszcze zmieścić w baterii
            stored = min(leftover, can_store)
            # Ładowanie tylko jeśli koszt energii z magazynu (po uwzględnieniu sprawności) jest niższy niż cena prądu
            koszt_energii_z_baterii = (1 / eff) * koszt_magazynowania
            if koszt_energii_z_baterii < cena_pradu:
                stan_baterii += stored
            else:
                total_from_network += leftover * cena_pradu  # sprzedajemy nadwyżkę

        # Pobieranie energii z magazynu w razie niedoboru, jeśli jest tańsze niż zakup z sieci
        if usage_remain > 0:
            available_from_batt = stan_baterii * eff
            koszt_energii_z_baterii = (1 / eff) * koszt_magazynowania
            # Porównanie kosztu energii z magazynu i z sieci
            if koszt_energii_z_baterii < cena_pradu:
                drawn = min(usage_remain, available_from_batt)
                stan_baterii -= (drawn / eff)
                usage_remain -= drawn
                used_direct += drawn
                total_from_battery += drawn
            else:
                # Gdy magazyn się nie opłaca, pobieramy energię z sieci
                total_from_network += usage_remain * cena_pradu
                used_direct += 0

        # Sumowanie energii pokrytej z PV i magazynu
        total_self_consumption += (usage - usage_remain)

    # Oblicz całkowity koszt energii (z sieci i z magazynu)
    koszt_energii_z_sieci = total_from_network
    koszt_energii_z_baterii = total_from_battery * koszt_magazynowania

    # Całkowite oszczędności: różnica między kosztem energii z sieci a rzeczywistym kosztem po magazynowaniu
    calkowite_oszczednosci = (roczne_zuzycie * cena_pradu) - (koszt_energii_z_sieci + koszt_energii_z_baterii) * 0.5

    return total_self_consumption, calkowite_oszczednosci



# ===================================================
# 1. Funkcja: wykonaj obliczenia i zwróć wyniki, wykresy
# ===================================================
def wykonaj_obliczenia(
        zuzycie_miesieczne,
        cena_pradu,
        powierzchnia_dachu,
        naslonecznienie,
        sprawnosc_paneli,
        moc_panelu,
        koszt_instalacji_kWp,
        dotacja_instalacja,
        wzrost_cen_pradu,
        czas_eksploatacji,
        uzycie_magazynu=False,
        pojemnosc_magazynu=0,
        sprawnosc_magazynu=1.0,
        koszt_magazynu=0,
        dotacja_magazyn=0,
        uzycie_pompy=False,
        zuzycie_pompa_rok=0,
        koszt_pompy=0,
        dotacja_pompy=0,
        cena_gazu=0,
        oszczednosc_gazu=0,
):
    # Obliczenia wstępne
    roczne_zuzycie = (zuzycie_miesieczne * 12) + (zuzycie_pompa_rok if uzycie_pompy else 0)
    powierzchnia_panelu = 1.7  # m², przyjęta stała
    liczba_paneli = int(powierzchnia_dachu // powierzchnia_panelu)
    moc_max = liczba_paneli * (moc_panelu / 1000.0)

    moc_wymagana = roczne_zuzycie / (naslonecznienie * sprawnosc_paneli)
    moc_instalacji = min(moc_max, moc_wymagana)

    energia_produkcja = moc_instalacji * naslonecznienie * sprawnosc_paneli

    # Koszty
    koszt_instalacji_netto = max(0, (moc_instalacji * koszt_instalacji_kWp) - dotacja_instalacja)

    # ZMIANA: Koszt magazynu to jednorazowy koszt (nie zależy od kWh * pojemność)
    if uzycie_magazynu:
        koszt_magazynu_netto = max(0, koszt_magazynu - dotacja_magazyn)
    else:
        koszt_magazynu_netto = 0

    koszt_pompy_netto = 0
    if uzycie_pompy:
        koszt_pompy_netto = max(0, koszt_pompy - dotacja_pompy)

    koszt_calosciowy = koszt_instalacji_netto + koszt_magazynu_netto + koszt_pompy_netto

    # --- Autokonsumpcja, jeśli używamy magazynu
    if uzycie_magazynu:
        energia_dostepna, calkowite_oszczednosci = symulacja_autokonsumpcji_z_baterią(
            roczne_zuzycie, energia_produkcja, cena_pradu,
            pojemnosc_magazynu, sprawnosc_magazynu
        )
    else:
        energia_dostepna = min(energia_produkcja, roczne_zuzycie)
        calkowite_oszczednosci = energia_dostepna * cena_pradu

    # Roczne oszczędności (1. rok)
    oszczednosci_pierwszy_rok = energia_dostepna * cena_pradu
    if uzycie_magazynu:
        oszczednosci_pierwszy_rok = calkowite_oszczednosci * 0.7  # 70% oszczędności z magazynu

    # Dodatkowe oszczędności z pompy ciepła (np. zastąpienie gazu)
    if uzycie_pompy:
        oszczednosci_pierwszy_rok += (oszczednosc_gazu * cena_gazu) - (zuzycie_pompa_rok*cena_pradu)

    # Okres zwrotu (bez uwzględniania wartości sprzedaży nadwyżki)
    if oszczednosci_pierwszy_rok > 0:
        okres_zwrotu = koszt_calosciowy / oszczednosci_pierwszy_rok
    else:
        okres_zwrotu = None

    # Oszczędności w kolejnych latach (uwzględniamy wzrost cen prądu)
    lata = np.arange(1, czas_eksploatacji + 1)
    oszczednosci_lata = oszczednosci_pierwszy_rok * ((1 + wzrost_cen_pradu) ** lata)
    oszczednosci_suma = np.cumsum(oszczednosci_lata)

    # --- Wykres 1: Oszczędności w czasie ---
    fig_savings = go.Figure()
    fig_savings.add_trace(go.Scatter(
        x=lata,
        y=oszczednosci_suma,
        mode='lines',
        name='Łączne oszczędności',
        line=dict(width=3, color='green')
    ))
    # Dodaj linię kosztów
    fig_savings.add_hline(y=koszt_calosciowy, line=dict(color='red', dash='dash'),
                          annotation_text="Koszt całkowity", annotation_position="top left")
    fig_savings.update_layout(
        title="Przewidywane oszczędności w czasie",
        xaxis_title="Lata",
        yaxis_title="Oszczędności (zł)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    # --- Wykres 2: Zużycie vs Produkcja ---
    fig_usage = go.Figure(data=[
        go.Bar(name='Roczne zużycie', x=['Energia (kWh)'], y=[roczne_zuzycie], marker_color='blue'),
        go.Bar(name='Roczna produkcja', x=['Energia (kWh)'], y=[energia_produkcja], marker_color='green')
    ])
    fig_usage.update_layout(
        barmode='group',
        title="Zużycie vs. Produkcja energii w skali roku",
        xaxis_title="Rodzaj",
        yaxis_title="kWh"
    )

    wyniki = {
        'moc_instalacji': moc_instalacji,
        'energia_produkcja': energia_produkcja,
        'koszt_calosciowy': koszt_calosciowy,
        'oszczednosci_pierwszy_rok': oszczednosci_suma[0],  # oszczędności w pierwszym roku
        'okres_zwrotu': okres_zwrotu,
        'fig_savings': fig_savings,
        'fig_usage': fig_usage,
        'pokrycie': (moc_instalacji >= (moc_wymagana - 0.01))  # czy w przybliżeniu pokrywa zużycie
    }
    return wyniki


# ===================================================
# 2. Zakładki w Streamlit
# ===================================================
tab1, tab2 = st.tabs(["Kalkulator", "Analiza danych"])

# ===================================================
# 2A. ZAKŁADKA 1: Wprowadzanie danych ręcznie
# ===================================================
with tab1:
    st.subheader("Kalkulator Opłacalności OZE")

    zuzycie_miesieczne = st.number_input("Średnie miesięczne zużycie energii (kWh)", 100, 5000, 350)
    cena_pradu = st.number_input("Cena prądu (zł/kWh)", 0.1, 2.0, 0.9, step=0.01)
    powierzchnia_dachu = st.number_input("Dostępna powierzchnia dachu (m²)", 5, 200, 40)
    naslonecznienie = st.number_input("Nasłonecznienie w regionie (kWh/m²/rok)", 800, 1500, 1100)
    sprawnosc_paneli = st.slider("Sprawność paneli (%)", 15, 22, 20) / 100
    moc_panelu = st.number_input("Moc pojedynczego panelu (Wp)", 200, 600, 400)
    koszt_instalacji_kWp = st.number_input("Koszt instalacji (zł/kWp)", 3000, 8000, 4500)
    dotacja_instalacja = st.number_input("Dotacja na instalację (zł)", 0, 30000, 5000)
    wzrost_cen_pradu = st.slider("Wzrost cen prądu (% rocznie)", 0, 10, 5) / 100
    czas_eksploatacji = st.slider("Czas eksploatacji instalacji (lata)", 10, 30, 25)

    st.write("---")

    st.subheader("Parametry magazynu energii")
    uzycie_magazynu = st.checkbox("Czy używasz magazynu energii?")
    if uzycie_magazynu:
        pojemnosc_magazynu = st.number_input("Pojemność magazynu (kWh)", 5, 100, 10)
        sprawnosc_magazynu = st.slider("Sprawność magazynu (%)", 80, 95, 90) / 100

        # ZMIANA: teraz prosimy o JEDNORAZOWY koszt magazynu (zł), a nie koszt/kWh
        koszt_magazynu = st.number_input("Jednorazowy koszt magazynu (zł)", 1000, 100000, 15000)
        dotacja_magazyn = st.number_input("Dotacja na magazyn (zł)", 0, 20000, 5000)
    else:
        pojemnosc_magazynu, sprawnosc_magazynu, koszt_magazynu, dotacja_magazyn = 0, 1, 0, 0

    st.subheader("Parametry pompy ciepła")
    uzycie_pompy = st.checkbox("Czy używasz pompy ciepła?")
    if uzycie_pompy:
        zuzycie_pompa_rok = st.number_input("Roczne zużycie energii przez pompę (kWh)", 500, 20000, 2000)
        koszt_pompy = st.number_input("Koszt pompy ciepła (zł)", 3000, 50000, 20000)
        dotacja_pompy = st.number_input("Dotacja na pompę ciepła (zł)", 0, 30000, 5000)
        cena_gazu = st.number_input("Cena gazu (zł/m³)", 2.0, 6.0, 3.5, step=0.01)
        oszczednosc_gazu = st.number_input("Roczna oszczędność gazu (m³)", 100, 5000, 1000)
    else:
        zuzycie_pompa_rok, koszt_pompy, dotacja_pompy, cena_gazu, oszczednosc_gazu = 0, 0, 0, 0, 0

    if st.button("Oblicz"):
        wyniki = wykonaj_obliczenia(
            zuzycie_miesieczne, cena_pradu, powierzchnia_dachu, naslonecznienie, sprawnosc_paneli,
            moc_panelu, koszt_instalacji_kWp, dotacja_instalacja, wzrost_cen_pradu, czas_eksploatacji,
            uzycie_magazynu, pojemnosc_magazynu, sprawnosc_magazynu, koszt_magazynu, dotacja_magazyn,
            uzycie_pompy, zuzycie_pompa_rok, koszt_pompy, dotacja_pompy, cena_gazu, oszczednosc_gazu,
        )

        st.write(f"🔋 **Moc instalacji:** {wyniki['moc_instalacji']:.2f} kWp")
        st.write(f"⚡ **Roczna produkcja energii:** {wyniki['energia_produkcja']:.0f} kWh")
        st.write(f"💰 **Łączny koszt inwestycji:** {wyniki['koszt_calosciowy']:.2f} zł")
        st.write(f"📉 **Roczne oszczędności (1. rok):** {wyniki['oszczednosci_pierwszy_rok']:.2f} zł")

        st.plotly_chart(wyniki['fig_savings'], use_container_width=True)
        st.plotly_chart(wyniki['fig_usage'], use_container_width=True)

        if not wyniki['pokrycie']:
            st.warning("⚠️ Instalacja **nie pokryje** całego zapotrzebowania na energię.")
        else:
            st.success("✅ Instalacja **pokryje** pełne zapotrzebowanie (lub wyprodukuje nadwyżkę).")

# ===================================================
# 2B. ZAKŁADKA 2: Przykładowe scenariusze (CSV/wbudowane)
# ===================================================
with tab2:
    st.subheader("Analiza na podstawie przykładowych scenariuszy")

    st.write("1) Możesz **wgrać własny plik CSV** zawierający zestaw scenariuszy.")
    st.write("2) Możesz **wybrać wbudowane scenariusze** (poniżej).")

    uploaded_file = st.file_uploader("Wgraj plik CSV z przykładowymi scenariuszami", type=['csv'])
    if uploaded_file is not None:
        df_input = pd.read_csv(uploaded_file)
        st.write("**Wczytano plik**:", uploaded_file.name)
        st.dataframe(df_input)
    else:
        data = {
            "scenario": [1, 2, 3],
            "zuzycie_miesieczne": [350, 300, 400],
            "cena_pradu": [0.9, 0.85, 1.0],
            "powierzchnia_dachu": [40, 30, 45],
            "naslonecznienie": [1100, 1000, 1200],
            "sprawnosc_paneli": [0.20, 0.18, 0.22],
            "moc_panelu": [400, 450, 400],
            "koszt_instalacji": [4500, 4000, 4800],
            "dotacja_instalacja": [5000, 4000, 6000],
            "wzrost_cen_pradu": [0.05, 0.03, 0.06],
            "czas_eksploatacji": [25, 20, 30],
            "uzycie_magazynu": [True, False, True],
            "pojemnosc_magazynu": [10, 0, 15],
            "sprawnosc_magazynu": [0.90, 1.0, 0.88],

            # ZMIANA: zamiast kosztu /kWh, jednorazowy koszt np. 15000 zł
            "koszt_magazynu": [15000, 0, 20000],
            "dotacja_magazyn": [5000, 0, 7000],

            "uzycie_pompy": [False, True, True],
            "zuzycie_pompa_rok": [0, 2000, 3000],
            "koszt_pompy": [0, 20000, 25000],
            "dotacja_pompy": [0, 5000, 10000],
            "cena_gazu": [0, 3.5, 3.5],
            "oszczednosc_gazu": [0, 1000, 1500]
        }
        df_input = pd.DataFrame(data)
        st.write("**Przykładowe scenariusze** (wbudowane):")
        st.dataframe(df_input)

    if st.button("Przetwórz scenariusze"):
        st.write("### Wyniki dla każdego scenariusza:")
        if 'df_input' in locals():
            for i, row in df_input.iterrows():
                wyniki = wykonaj_obliczenia(
                    row["zuzycie_miesieczne"],
                    row["cena_pradu"],
                    row["powierzchnia_dachu"],
                    row["naslonecznienie"],
                    row["sprawnosc_paneli"],
                    row["moc_panelu"],
                    row["koszt_instalacji"],
                    row["dotacja_instalacja"],
                    row["wzrost_cen_pradu"],
                    row["czas_eksploatacji"],
                    row["uzycie_magazynu"],
                    row["pojemnosc_magazynu"],
                    row["sprawnosc_magazynu"],
                    row["koszt_magazynu"],
                    row["dotacja_magazyn"],
                    row["uzycie_pompy"],
                    row["zuzycie_pompa_rok"],
                    row["koszt_pompy"],
                    row["dotacja_pompy"],
                    row["cena_gazu"],
                    row["oszczednosc_gazu"]
                )

                st.markdown(f"#### Scenariusz: {row.get('scenario', i + 1)}")
                st.write(f"🔋 **Moc instalacji**: {wyniki['moc_instalacji']:.2f} kWp")
                st.write(f"⚡ **Roczna produkcja**: {wyniki['energia_produkcja']:.0f} kWh")
                st.write(f"💰 **Koszt całkowity**: {wyniki['koszt_calosciowy']:.2f} zł")
                st.write(f"📉 **Oszczędności (1. rok)**: {wyniki['oszczednosci_pierwszy_rok']:.2f} zł")

                with st.expander(f"Wykresy scenariusza {row.get('scenario', i + 1)}"):
                    st.plotly_chart(wyniki['fig_savings'], use_container_width=True, key=f"savings_{i}")
                    st.plotly_chart(wyniki['fig_usage'], use_container_width=True, key=f"usage_{i}")

                if not wyniki['pokrycie']:
                    st.warning("⚠️ Instalacja nie pokryje pełnego zapotrzebowania.")
                else:
                    st.success("✅ Instalacja pokrywa zapotrzebowanie na energię.")

                st.write("---")
