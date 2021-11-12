config = {
    # aanschafkosten is ex btw, die kan je terugvragen
    "aanschafkosten": 6805,

    "jaren": 25,
    "aantal_panelen": 12,
    "paneel_vermogen": 400,
    "hypotheek_rente": 2.0,

    # verbruik is het verwacht aantal kWH per maand
    "verbruik": [278, 247, 267, 246, 246, 217, 221, 185, 186, 235, 276, 371],

    # Is de na 25 jaar minimale rendement aldus fabrikant
    "verwacht_eind_rendement": 0.92,

    # Is het realistisch rendement van een paneel
    "verwacht_vermogen_percentage": 0.85,

    # percentage van de opgewekte stroom die je zelf kan gebruiken, de rest wordt teruggeleverd aan het net
    "eigen_verbruik_percentage": 0.3,

    # Hoeveel procent van het verbruik je in welke maand opwekt (alles bij elkaar = 1)
    # Bron: milieucentraal.nl
    "opbrengst_percentage_per_maand": [0.03, 0.05, 0.08, 0.12, 0.13, 0.13, 0.13, 0.11, 0.10, 0.07, 0.03, 0.02],

    # Salderingspercentage over de jaren (geen waarde = 0%)
    # Eerste jaar is 2022
    "salderings_percentage": [1, 0.91, 0.82, 0.73, 0.64, 0.55, 0.46, 0.37, 0.28],

    # Bedrag dat energieleverancier betaald per teruggeleverde kWh (die niet gesaldeerd zijn)
    "terugleververgoeding": 0.06,

    # Prijs per kWh
    "prijs_per_kwh": 0.23
}


class ZonnepaneelBerekening:

    def __init__(self, cfg):
        self.cfg = cfg

    def bereken_maandelijkse_hypotheek(self):
        maandelijkse_aflossing = self.cfg["aanschafkosten"] / (self.cfg["jaren"] * 12)
        resterende_schuld = self.cfg["aanschafkosten"]
        betalingen = []
        for maand in range(self.cfg["jaren"] * 12):
            rente_betaling = resterende_schuld * (self.cfg["hypotheek_rente"] / 100) / 12
            betalingen.append(round(maandelijkse_aflossing + rente_betaling, 2))
            resterende_schuld -= maandelijkse_aflossing
        return betalingen

    def bereken_maandelijks_opwekking(self):
        afname_rendement_per_maand = (1 - self.cfg["verwacht_eind_rendement"]) / (self.cfg["jaren"] * 12)
        totale_afname = 0
        kwhs = []
        for jaar in range(self.cfg["jaren"]):
            for maand in range(12):
                totale_afname += afname_rendement_per_maand
                ideaal_vermogen = self.cfg["paneel_vermogen"] * (1 - totale_afname)
                realistisch_vermogen = ideaal_vermogen * self.cfg["verwacht_vermogen_percentage"] * \
                                       self.cfg["opbrengst_percentage_per_maand"][maand]
                kwhs.append(round(realistisch_vermogen * self.cfg["aantal_panelen"]))

        return kwhs

    def bereken_maandelijks_verbruik(self):
        verbruik_per_maand = []
        for jaar in range(self.cfg["jaren"]):
            for maand in range(12):
                verbruik_per_maand.append(self.cfg["verbruik"][(jaar * 12 + maand) % 12])

        return verbruik_per_maand

    def bereken_maandelijks_eigen_verbruik(self, maandelijkse_opwekking: [int]):
        eigen_verbruik = []
        teruggeleverd = []
        for idx, opwekking in enumerate(maandelijkse_opwekking):
            eigen_verbruik.append(round(opwekking * self.cfg["eigen_verbruik_percentage"]))
            teruggeleverd.append(round(opwekking * (1 - self.cfg["eigen_verbruik_percentage"])))

        return eigen_verbruik, teruggeleverd

    # De saldering wordt berekend over de jaartotalen, niet het maandelijks verbruik
    def bereken_jaarlijkse_saldering_en_teruglevering(self, eigen_verbruik: [int], teruggeleverd: [int]):
        totaal_verbruik_per_jaar = sum(self.cfg["verbruik"])
        saldering = []
        normaal_teruggeleverd = []

        for jaar in range(self.cfg["jaren"]):
            # Het salderings percentage neemt af over de jaren en is op een bepaald moment 0
            salderings_percentage = self.cfg["salderings_percentage"][jaar] if jaar < len(
                self.cfg["salderings_percentage"]) else 0

            # Berekening hoeveel is teruggeleverd en zelf verbruikt over het hele jaar
            maand_range = slice(jaar * 12, jaar * 12 + 12)
            teruggeleverd_jaar_totaal = sum(teruggeleverd[maand_range])
            eigen_verbruik_jaar_totaal = sum(eigen_verbruik[maand_range])

            # Het max te salderen getal neemt heel licht toe, dit komt omdat oudere panelen
            # minder opleveren waardoor meer stroom afgenomen wordt van het netwerk
            max_salderen = totaal_verbruik_per_jaar - eigen_verbruik_jaar_totaal

            te_salderen = round(min(teruggeleverd_jaar_totaal, max_salderen) * salderings_percentage)

            # Over het restant (dwz niet gesaldeerd) moet de energieleverancier een redelijke vergoeding betalen
            restant = teruggeleverd_jaar_totaal - te_salderen

            saldering.append(te_salderen)
            normaal_teruggeleverd.append(restant)

        return saldering, normaal_teruggeleverd

    def print_alles(
            self,
            hypotheek: [float],
            maandelijkse_verbruik: [int],
            maandelijks_eigen_verbruik: [int],
            opwekking_kwh: [int],
            jaarselijkse_saldering: [int],
            jaarlijks_teruggeleverd: [int]
    ):
        totale_winst = 0

        for jaar in range(self.cfg["jaren"]):
            print("")
            print("Jaar"
                  " | Maand"
                  " | Hypotheek"
                  " | Verbruikt kWh"
                  " | Eigen verbruik kWh"
                  " | Opgewekt kWh"
                  )

            for maand in range(12):
                i = jaar * 12 + maand
                print(f"{2022 + jaar:>4}"
                      f" | {1 + maand:>5}"
                      f" | {'{:.2f}'.format(hypotheek[i]):>9}"
                      f" | {maandelijkse_verbruik[i]:>13}"
                      f" | {maandelijks_eigen_verbruik[i]:>18}"
                      f" | {opwekking_kwh[i]:>12}"
                      )

            maand_range = slice(jaar * 12, jaar * 12 + 12)
            totaal_verbruik = sum(maandelijkse_verbruik[maand_range])
            totaal_opwekking = sum(opwekking_kwh[maand_range])
            totaal_eigen_verbruik = sum(maandelijks_eigen_verbruik[maand_range])
            net_verbruik = totaal_verbruik - totaal_eigen_verbruik - jaarselijkse_saldering[jaar]

            print("")
            print(f"{2022 + jaar}")
            print("-------------------------------")
            print(f"Verbruik {totaal_verbruik:>18} kWh")
            print(f"Opwekking {totaal_opwekking:>17} kWh")
            print(f"Eigen verbruik {totaal_eigen_verbruik:>12} kWh")
            print(f"Net verbruik min sal. {net_verbruik:>5} kWh")
            print(f"Saldering {jaarselijkse_saldering[jaar]:>17} kWh")
            print(f"Teruggeleverd {jaarlijks_teruggeleverd[jaar]:>13} kWh")

            totale_hypotheek = sum(hypotheek[maand_range]) * -1
            opbrengst_teruggeleverd = jaarlijks_teruggeleverd[jaar] * self.cfg["terugleververgoeding"]
            kosten_net_verbruik = net_verbruik * self.cfg["prijs_per_kwh"] * -1

            print("-------------------------------")
            print(f"Hypotheek {'€ {:.2f}'.format(totale_hypotheek):>21}")
            print(f"Teruggeleverd {'€ {:.2f}'.format(opbrengst_teruggeleverd):>17}")
            print(f"Net verbruik min sal. {'€ {:.2f}'.format(kosten_net_verbruik):>8}")

            totale_kosten = totale_hypotheek + opbrengst_teruggeleverd + kosten_net_verbruik
            normale_kosten = totaal_verbruik * self.cfg["prijs_per_kwh"] * -1
            winst = totale_kosten - normale_kosten

            print("-------------------------------")
            print(f"Totaal {'€ {:.2f}'.format(totale_kosten):>24}")
            print(f"Geen panelen {'€ {:.2f}'.format(normale_kosten):>18}")
            print(f"Winst {'€ {:.2f}'.format(winst):>25}")

            totale_winst += winst

        print("\n\n\n")
        print("======== Over 25 jaar =========")
        print(f"Winst {'€ {:.2f}'.format(totale_winst):>25}")

    def bereken_alles(self):
        maandelijkse_hypotheek_betalingen = self.bereken_maandelijkse_hypotheek()

        maandelijkse_opwekking = self.bereken_maandelijks_opwekking()

        maandelijkse_verbruik = self.bereken_maandelijks_verbruik()

        maandelijks_eigen_verbruik, maandelijks_teruggeleverd = self.bereken_maandelijks_eigen_verbruik(
            maandelijkse_opwekking)

        jaarselijkse_saldering, jaarlijks_teruggeleverd = self.bereken_jaarlijkse_saldering_en_teruglevering(
            maandelijks_eigen_verbruik, maandelijks_teruggeleverd)

        self.print_alles(
            maandelijkse_hypotheek_betalingen,
            maandelijkse_verbruik,
            maandelijks_eigen_verbruik,
            maandelijkse_opwekking,
            jaarselijkse_saldering,
            jaarlijks_teruggeleverd,
        )


def main():
    berekening = ZonnepaneelBerekening(config)
    berekening.bereken_alles()


if __name__ == "__main__":
    main()
