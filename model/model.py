import copy

from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
from model.escursione import Escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi
        self.escursioni_punto_interesse = []

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        self.escursioni_punto_interesse=EscursioneDAO.get_escursioni_punti_interesse()

        for escursione in self.escursioni_map.values():
            escursione.punti_interesse = set()

        for punto in self.punti_interesse_map.values():
            punto.escursioni = set()

        for relazione in self.escursioni_punto_interesse:
            escursione = self.escursioni_map.get(relazione["id_escursione"])
            punto = self.punti_interesse_map.get(relazione["id_punto_interesse"])

            escursione.punti_interesse.add(punto)
            punto.escursioni.add(escursione)

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        self.max_giorni = max_giorni
        self.max_budget = max_budget
        self.escursioni_disponibili = []
        for escursione in self.escursioni_map.values():
            if id_parco==escursione.id_parco:
                self.escursioni_disponibili.append(escursione)




        self._ricorsione(0,[],0,0,0,set())



        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        if valore_corrente>self._valore_ottimo:
            self._pacchetto_ottimo=pacchetto_parziale.copy()
            self._costo=costo_corrente
            self._valore_ottimo=valore_corrente


        for i in range(start_index, len(self.escursioni_disponibili)):
            escursione=self.escursioni_disponibili[i]

            if self._vincoli_soddisfatti(escursione,pacchetto_parziale,durata_corrente,costo_corrente, punti_usati):
                pacchetto_parziale.append(escursione)
                pt_interesse=self._get_punti_escursione(escursione)
                for punto in pt_interesse:
                    punti_usati.add(punto)
                valore_escursione=self._calcola_valore(escursione)

                self._ricorsione(i+1,pacchetto_parziale,durata_corrente+escursione.durata_giorni,costo_corrente+escursione.costo,valore_corrente+valore_escursione,punti_usati)
                pacchetto_parziale.pop()
                punti_usati.difference_update(pt_interesse)

    def _get_punti_escursione(self, escursione):
        punti_nuova_escursione = set()
        for punto in escursione.punti_interesse:
            punti_nuova_escursione.add(punto.id)
        return punti_nuova_escursione


    def _calcola_valore(self,escursione):
        somma_val=0
        for punto in escursione.punti_interesse:
            somma_val += punto.voto_visitatori
        return somma_val


    def _vincoli_soddisfatti(self,escursione,pacchetto_parziale,durata_corrente,costo_corrente, punti_usati):

        # Vincolo 1: Le escursioni incluse nel pacchetto devono essere tutte diverse tra loro.
        for elemento in pacchetto_parziale:
            if elemento.id==escursione.id:
                return False

        # Vincolo 2 Non devono esserci punti di interesse duplicati all'interno del pacchetto (non si visita due volte lo stesso punto di interesse).

        punti_nuova_escursione=self._get_punti_escursione(escursione)
        for punto_id in punti_nuova_escursione:
            if punto_id in punti_usati:
                return False

        # Vincolo 3: La durata complessiva del pacchetto non deve superare il numero massimo di giorni indicato (G).
        # Vincolo 4: Il costo totale del pacchetto non deve eccedere il budget massimo previsto (B).

        durata=durata_corrente+escursione.durata_giorni
        costo=costo_corrente+escursione.costo

        if self.max_giorni is not None and durata>self.max_giorni:
            return False

        if self.max_budget is not None and costo>self.max_budget:
            return False

        return True

