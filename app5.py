import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------
# Ustawienia strony
# ----------------------------------------------------
st.set_page_config(page_title="Kalkulator Fotowoltaiki", layout="wide")

# ----------------------------------------------------
# Funkcja: wykonaj obliczenia i zwróć wyniki + wykresy
# ----------------------------------------------------
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
):
    # Roczne zużycie energii -> sumujemy pompę ciepła (jeśli używana)
    roczne_zuzycie = (zuzycie_miesieczne * 12) + (zuzycie_pompa_rok if uzycie_pompy else 0)

    # Podstawowe obliczenia PV
    powierzchnia_panelu = 1.7  # przykładowa powierzchnia 1 panelu
    liczba_paneli = int(powierzchnia_dachu // powierzchnia_panelu)
    moc_max = liczba_paneli * (moc_panelu / 1000.0)

    moc_wymagana = roczne_zuzycie / (naslonecznienie * sprawnosc_paneli)
    moc_instalacji = min(moc_max, moc_wymagana)

    energia_produkcja = moc_instalacji * naslonecznienie * sprawnosc_paneli

    # Koszty instalacji (po dotacji)
    koszt_instalacji_netto = max(0, (moc_instalacji * koszt_instalacji_kWp) - dotacja_instalacja)

    # Koszt magazynu (po dotacji)
    koszt_magazynu_netto = 0
    if uzycie_magazynu:
        koszt_magazynu_netto = max(0, (pojemnosc_magazynu * koszt_magazynu) - dotacja_magazyn)

    # Koszt pompy ciepła (po dotacji)
    koszt_pompy_netto = 0
    if uzycie_pompy:
        koszt_pompy_netto = max(0, koszt_pompy - dotacja_pompy)

    # Łączny koszt
    koszt_calosciowy = koszt_instalacji_netto + koszt_magazynu_netto + koszt_pompy_netto

    # Oszczędności (1. rok)
    energia_dostepna = min(energia_produkcja, roczne_zuzycie)
    oszczednosci_pierwszy_rok = energia_dostepna * cena_pradu

    # Okres zwrotu
    if oszczednosci_pierwszy_rok > 0:
        okres_zwrotu = koszt_calosciowy / oszczednosci_pierwszy_rok
    else:
        okres_zwrotu = None

    # Oszczędności w czasie (z uwzględnieniem wzrostu cen)
    lata = np.arange(1, czas_eksploatacji + 1)
    oszczednosci_lata = oszczednosci_pierwszy_rok * ((1 + wzrost_cen_pradu) ** lata)
    oszczednosci_suma = np.cumsum(oszczednosci_lata)

    # Wykres 1: Oszczędności w czasie
    fig_savings = go.Figure()
    fig_savings.add_trace(go.Scatter(
        x=lata,
        y=oszczednosci_suma,
        mode='lines',
        name='Łączne oszczędności',
        line=dict(width=3, color='green')
    ))
    fig_savings.add_hline(
        y=koszt_calosciowy,
        line=dict(color='red', dash='dash'),
        annotation_text="Koszt całkowity",
        annotation_position="top left"
    )
    fig_savings.update_layout(
        title="Przewidywane oszczędności w czasie",
        xaxis_title="Lata",
        yaxis_title="Oszczędności (zł)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    # Wykres 2: Zużycie vs Produkcja
    fig_usage = go.Figure(data=[
        go.Bar(name='Roczne zużycie', x=['Energia (kWh)'], y=[roczne_zuzycie], marker_color='blue'),
        go.Bar(name='Roczna produkcja', x=['Energia (kWh)'], y=[energia_produkcja], marker_color='green')
    ])
    fig_usage.update_layout(
        barmode='group',
        title="Zużycie vs. Produkcja energii (rocznie)",
        xaxis_title="Rodzaj",
        yaxis_title="kWh"
    )

    # Czy instalacja pokrywa zapotrzebowanie (w przybliżeniu)?
    pokrycie = (moc_instalacji >= moc_wymagana - 0.01)

    wyniki = {
        "moc_instalacji": moc_instalacji,
        "energia_produkcja": energia_produkcja,
        "koszt_calosciowy": koszt_calosciowy,
        "oszczednosci_pierwszy_rok": oszczednosci_pierwszy_rok,
        "okres_zwrotu": okres_zwrotu,
        "fig_savings": fig_savings,
        "fig_usage": fig_usage,
        "pokrycie": pokrycie
    }
    return wyniki


# ----------------------------------------------------
# Tworzymy zakładki
# ----------------------------------------------------
tab1, tab2 = st.tabs(["Manualne dane", "Przykładowe scenariusze"])

# ----------------------------------------------------
# ZAKŁADKA 1: Manualne dane (powrót do starego widoku)
# ----------------------------------------------------
with tab1:
    st.sidebar.header("Dane wejściowe (manualne)")

    # Sidebar: parametry główne
    zuzycie_miesieczne = st.sidebar.number_input("Średnie miesięczne zużycie energii (kWh)", 100, 5000, 350)
    cena_pradu = st.sidebar.number_input("Cena prądu (zł/kWh)", 0.1, 2.0, 0.9, step=0.01)
    powierzchnia_dachu = st.sidebar.number_input("Dostępna powierzchnia dachu (m²)", 5, 200, 40)
    naslonecznienie = st.sidebar.number_input("Nasłonecznienie w regionie (kWh/m²/rok)", 800, 1500, 1100)
    sprawnosc_paneli = st.sidebar.slider("Sprawność paneli (%)", 15, 22, 20) / 100
    moc_panelu = st.sidebar.number_input("Moc pojedynczego panelu (Wp)", 200, 600, 400)
    koszt_instalacji_kWp = st.sidebar.number_input("Koszt instalacji (zł/kWp)", 3000, 8000, 4500)
    dotacja_instalacja = st.sidebar.number_input("Dotacja na instalację (zł)", 0, 30000, 5000)
    wzrost_cen_pradu = st.sidebar.slider("Wzrost cen prądu (% rocznie)", 0, 10, 5) / 100
    czas_eksploatacji = st.sidebar.slider("Czas eksploatacji instalacji (lata)", 10, 30, 25)

    # Sidebar: magazyn energii
    st.sidebar.subheader("Magazyn energii")
    uzycie_magazynu = st.sidebar.checkbox("Czy używasz magazynu energii?")
    if uzycie_magazynu:
        pojemnosc_magazynu = st.sidebar.number_input("Pojemność magazynu (kWh)", 5, 100, 10)
        sprawnosc_magazynu = st.sidebar.slider("Sprawność magazynu (%)", 80, 95, 90) / 100
        koszt_magazynu = st.sidebar.number_input("Koszt magazynu (zł/kWh)", 1500, 10000, 3000)
        dotacja_magazyn = st.sidebar.number_input("Dotacja na magazyn (zł)", 0, 20000, 5000)
    else:
        pojemnosc_magazynu, sprawnosc_magazynu, koszt_magazynu, dotacja_magazyn = 0, 1, 0, 0

    # Sidebar: pompa ciepła
    st.sidebar.subheader("Pompa ciepła")
    uzycie_pompy = st.sidebar.checkbox("Czy używasz pompy ciepła?")
    if uzycie_pompy:
        zuzycie_pompa_rok = st.sidebar.number_input("Roczne zużycie energii przez pompę (kWh)", 500, 20000, 2000)
        koszt_pompy = st.sidebar.number_input("Koszt pompy ciepła (zł)", 3000, 50000, 20000)
        dotacja_pompy = st.sidebar.number_input("Dotacja na pompę ciepła (zł)", 0, 30000, 5000)
    else:
        zuzycie_pompa_rok, koszt_pompy, dotacja_pompy = 0, 0, 0

    # -------------------------------------------
    # Wyniki kalkulacji w głównej części ekranu
    # (liczone na bieżąco, bez przycisku)
    # -------------------------------------------
    st.header("Wyniki kalkulacji (od razu)")

    wyniki = wykonaj_obliczenia(
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
        uzycie_magazynu,
        pojemnosc_magazynu,
        sprawnosc_magazynu,
        koszt_magazynu,
        dotacja_magazyn,
        uzycie_pompy,
        zuzycie_pompa_rok,
        koszt_pompy,
        dotacja_pompy
    )

    st.write(f"**Moc instalacji (PV)**: {wyniki['moc_instalacji']:.2f} kWp")
    st.write(f"**Roczna produkcja energii**: {wyniki['energia_produkcja']:.0f} kWh")
    st.write(f"**Łączny koszt inwestycji**: {wyniki['koszt_calosciowy']:.2f} zł")
    st.write(f"**Oszczędności (1. rok)**: {wyniki['oszczednosci_pierwszy_rok']:.2f} zł")

    if wyniki['okres_zwrotu']:
        if wyniki['okres_zwrotu'] < czas_eksploatacji:
            st.write(f"**Okres zwrotu**: {wyniki['okres_zwrotu']:.1f} lat")
        else:
            st.warning("⚠️ Instalacja **nie zwróci się** w zakładanym czasie eksploatacji.")
    else:
        st.warning("⚠️ Brak oszczędności w pierwszym roku (okres zwrotu ∞).")

    # Wykresy
    st.plotly_chart(wyniki['fig_savings'], use_container_width=True)
    st.plotly_chart(wyniki['fig_usage'], use_container_width=True)

    if not wyniki['pokrycie']:
        st.warning("Instalacja **nie pokryje** pełnego zapotrzebowania na energię.")
    else:
        st.success("Instalacja **pokryje** pełne zapotrzebowanie na energię (lub wyprodukuje nadwyżkę).")


# ----------------------------------------------------
# ZAKŁADKA 2: Przykładowe scenariusze (CSV/wbudowane)
# ----------------------------------------------------
with tab2:
    st.subheader("Analiza na podstawie przykładowych scenariuszy")

    st.write("1) Możesz **wgrać własny plik CSV** zawierający zestaw scenariuszy.")
    st.write("2) Możesz **wybrać wbudowane scenariusze** (poniżej).")

    # 1. Wgranie pliku CSV
    uploaded_file = st.file_uploader("Wgraj plik CSV z przykładowymi scenariuszami", type=["csv"])

    if uploaded_file is not None:
        df_input = pd.read_csv(uploaded_file)
        st.write("**Wczytano plik**:", uploaded_file.name)
        st.dataframe(df_input)
    else:
        # 2. Wbudowane scenariusze
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
            "koszt_magazynu": [3000, 0, 3500],
            "dotacja_magazyn": [5000, 0, 7000],
            "uzycie_pompy": [False, True, True],
            "zuzycie_pompa_rok": [0, 2000, 3000],
            "koszt_pompy": [0, 20000, 25000],
            "dotacja_pompy": [0, 5000, 10000],
        }
        df_input = pd.DataFrame(data)
        st.write("**Przykładowe scenariusze** (wbudowane):")
        st.dataframe(df_input)

    # Przycisk do przetworzenia scenariuszy
    if st.button("Przetwórz scenariusze"):
        if 'df_input' in locals():
            st.write("### Wyniki dla każdego scenariusza:")
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
                )

                st.markdown(f"#### Scenariusz: {row.get('scenario', i+1)}")
                st.write(f"- **Moc instalacji**: {wyniki['moc_instalacji']:.2f} kWp")
                st.write(f"- **Roczna produkcja**: {wyniki['energia_produkcja']:.0f} kWh")
                st.write(f"- **Koszt całkowity**: {wyniki['koszt_calosciowy']:.2f} zł")
                st.write(f"- **Oszczędności (1. rok)**: {wyniki['oszczednosci_pierwszy_rok']:.2f} zł")

                if wyniki['okres_zwrotu']:
                    st.write(f"- **Okres zwrotu**: {wyniki['okres_zwrotu']:.1f} lat")
                else:
                    st.write("- **Okres zwrotu**: brak (niskie oszczędności)")

                # Rozwijana sekcja z wykresami
                with st.expander(f"Wykresy scenariusza {row.get('scenario', i+1)}"):
                    st.plotly_chart(wyniki['fig_savings'], use_container_width=True)
                    st.plotly_chart(wyniki['fig_usage'], use_container_width=True)

                if not wyniki['pokrycie']:
                    st.warning("⚠️ Instalacja nie pokryje pełnego zapotrzebowania.")
                else:
                    st.success("✅ Instalacja pokrywa zapotrzebowanie na energię.")

                st.write("---")
