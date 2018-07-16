# -*- coding: utf-8 -*-
"""
Python-Modul zum Einlesen von Gemeindeverzeichnisdaten des Statistischen Bundesamts als pandas DataFrame.
Daten müssen als GV100 im ASCII-Format vorliegen.
Download der Daten unter:
https://www.destatis.de/DE/ZahlenFakten/LaenderRegionen/Regionales/Gemeindeverzeichnis/Gemeindeverzeichnis.html

Für den Unterschied zw. Amtl. Gemeindeschlüssel (AGS) und Amtl. Regionalschlüssel (ARS) siehe
https://de.wikipedia.org/wiki/Amtlicher_Gemeindeschl%C3%BCssel.

April 2016 / August 2017 (Update)
Markus Konrad <markus.konrad@wzb.eu>
"""

from io import StringIO
from collections import OrderedDict

import pandas as pd

VERZ_DATEI_ENC = 'iso-8859-1'
VERZ_DATEI_SPALTEN_BREITE = OrderedDict([
    ('satzart', 2),
    ('stand', 8),
    ('ags', 8),                # amtl. Gemeindeschlüssel
    ('gemeinde_verb', 4),
    ('gemeinde_bez', 50),
    ('leer_1', 50),
    ('schluesselfelder', 6),
    ('flaeche_ha', 11),
    ('bevoelkerung_ges', 11),
    ('bevoelkerung_maennl', 11),
    ('leer_2', 4),
    ('plz', 5),
    ('plz_eindeutig', 5),
    ('leer_3', 2),
    ('finanzamts_bezirk', 4),
    ('gerichtsbarkeit', 4),
    ('arbeitsagentur_bezirk', 5),
    ('bundestagswahlkreise_von', 3),
    ('bundestagswahlkreise_bis', 3),
    ('leer_4', 4),
    ('bemerkungen', 20)
])

VERZ_DATEI_SPALTEN_TYP = {
    'stand': str,
    'ags': str,
    'gemeinde_verb': str,
    'plz': str,
    'plz_eindeutig': lambda v: not bool(v),
    'finanzamts_bezirk': str,
    'gerichtsbarkeit': str,
    'arbeitsagentur_bezirk': str,
    'bundestagswahlkreise_von': int,
    'bundestagswahlkreise_bis': int,
    'bemerkungen': str,
}

VERZ_DATEI_SPALTEN_ZU_INT = (
    'schluesselfelder',
    'bevoelkerung_ges',
    'bevoelkerung_maennl',
)

VERZ_DATEI_STAND_SPALTEN_IDX = [1]

SATZART = [art for art in range(10, 61, 10)]   # wird in string umgewandelt


#%%

def einlesen(datei, kodierung=None, satzart=None, bl_praefix_hinzufuegen=False, spalten_zu_int=True,
             ars_erzeugen=True):
    """
    Gemeindeverzeichnisdaten aus Datei `datei` einlesen. Daten müssen als GV100 im ASCII-Format vorliegen.
    `kodierung` gibt Dateikodierung an (standardmäßig 'iso-8859-1')
    `satzart` gibt Datensatzart(en) an, welche ausgelesen werden sollen (standardmäßig sämtliche Satzarten). Kann ein
    eine einzelne Zahl/String oder eine Liste / ein Tupel von Zahlen/Strings sein. Gültige Satzarten sind 10, 20, ...
    60.
    `bl_praefix_hinzufuegen` gibt an, ob eine Spalte "reg_schluessel_bl_praefix" hinzugefügt werden soll, welche
      nur den Bundeslandpräfix des Regionalschlüsselsenthält.
    `spalten_zu_int`: Listen von Spalten, welche zu Integer-Werten umgewandelt werden sollen. Achtung, NAs werden dabei
    zu -1! Standardwert: True -> Standardspalten von VERZ_DATEI_SPALTEN_ZU_INT werden zu Integern umgewandelt.
    `ars_erzeugen`: Wenn True, dann aus achtstelligem AGS (Amtl. Gemeindeschlüssel) auch zwölfstelligen ARS
    (Amtl. Regionalschlüssel) erzeugen.
    """    
    kodierung = kodierung or VERZ_DATEI_ENC
    satzart = satzart or SATZART

    if isinstance(satzart, int) or isinstance(satzart, str):
        satzart = [satzart]

    if spalten_zu_int is True:
        spalten_zu_int = VERZ_DATEI_SPALTEN_ZU_INT

    zeilen_buf = _gemeindedatenzeilen(datei, kodierung, satzart)
    
    gem_vz = _gemeindedaten_tabelle(zeilen_buf,
                                    VERZ_DATEI_SPALTEN_BREITE,
                                    VERZ_DATEI_SPALTEN_TYP,
                                    VERZ_DATEI_STAND_SPALTEN_IDX)
    zeilen_buf.close()

    if ars_erzeugen:
        maske_gemeinden = ~gem_vz.gemeinde_verb.isnull() & (gem_vz.satzart == 60)
        ags_land_rb_kreis = gem_vz.loc[maske_gemeinden, 'ags'].str.slice(0, 5)
        ags_gem = gem_vz.loc[maske_gemeinden, 'ags'].str.slice(-3)
        gem_vz['ars'] = ags_land_rb_kreis.str.cat(gem_vz.loc[maske_gemeinden, 'gemeinde_verb']).str.cat(ags_gem)
        assert sum(~gem_vz.ars.isnull()) == len(ags_land_rb_kreis) == len(ags_gem)
        assert set(gem_vz.loc[~gem_vz.ars.isnull(), 'ars'].str.len()) == {12}

    if spalten_zu_int:
        for sp in spalten_zu_int:
            gem_vz.loc[:, sp] = _zu_int_var(gem_vz.loc[:, sp])
    
    if bl_praefix_hinzufuegen:
        gem_vz['reg_schluessel_bl_praefix'] = gem_vz['reg_schluessel'].apply(lambda s: s[:2])
    
    return gem_vz


def ort_ohne_suffix(bez):
    """
    Entfernt ", Stadt"-Suffix aus Gemeindebezeichnung
    """
    idx = bez.find(', Stadt')
    if idx > 0:
        return bez[:idx]
    else:
        return bez


def reg_schluessel_ermitteln(gem_vz, df, spalte_plz, spalte_ort, spalte_reg_schluessel=None,
                             gem_vz_reg_schluessel='ags'):
    """
    Versuche für Orte mit PLZ in einem DataFrame `df` die passenden Gemeinden aus dem Gemeindeverzeichnis
    `gem_vz` und deren Regionalschlüssel zu ermitteln.
    `spalte_plz` bezeichnet die Spalte mit den PLZ in `df`
    `spalte_ort` bezeichnet die Spalte mit den Orten in `df`
    `spalte_reg_schluessel` bezeichnet die Spalte, in welche der ermittelte Regionalschlüssel gespeichert wird
    (Spalte wird in `df` angelegt)
    `gem_vz_reg_schluessel` gibt an, welche Spalte aus `gem_vz` als Regionalschlüssel verwendet werden soll. Standard
    ist 'ags' (z.B. auch 'ars' verwendbar).
    
    Gibt Kopie des aktualisierten `df` mit zusätzlichem Regionalschlüssel zurück.
    """
    if not spalte_reg_schluessel:
        spalte_reg_schluessel = gem_vz_reg_schluessel
    
    n_zeilen_initial = len(df)
    
    df = df.copy()
    
    # alle Daten aus Gemeindeverz. bei dem die PLZ übereinstimmt
    vz_via_plz = gem_vz[gem_vz.plz.isin(df[spalte_plz])].copy()
    
    # ", Stadt"-Suffix entfernen und als "ort" Spalte speichern
    vz_via_plz['ort'] = vz_via_plz['gemeinde_bez'].apply(ort_ohne_suffix)
    
    # Versuch 1: Übereinstimmung PLZ und Ort (ohne Suffix)
    orte_reg_schluessel1 = vz_via_plz.loc[vz_via_plz.ort.isin(set(df[spalte_ort])), [gem_vz_reg_schluessel, 'plz', 'ort']]
    tmp = pd.merge(df, orte_reg_schluessel1,
                   how='left',
                   left_on=[spalte_plz, spalte_ort],
                   right_on=['plz', 'ort'])[gem_vz_reg_schluessel]
    tmp.name = spalte_reg_schluessel
    tmp.index = df.index
    df = pd.concat((df, tmp), axis=1)
    
    unbekannte = df[df[spalte_reg_schluessel].isnull()]
    
    if len(unbekannte) == 0:
        assert n_zeilen_initial == len(df)
        return df
    
    # Versuch 2: Bei weiteren Unbekannten muss PLZ übereinstimmen und Ortsname nur noch enthalten sein
    orte_reg_schluessel2 = {}
    for index, zeile in unbekannte.iterrows():
        match = vz_via_plz[(vz_via_plz.plz == zeile[spalte_plz]) & (vz_via_plz.ort.str.contains(zeile[spalte_ort]))]
        if len(match) > 0:
             orte_reg_schluessel2[index] = match.sample()[gem_vz_reg_schluessel].values[0]
    tmp = pd.Series(orte_reg_schluessel2)
    tmp.name = spalte_reg_schluessel
    df.update(tmp)
    
    unbekannte = df[df[spalte_reg_schluessel].isnull()]
    
    if len(unbekannte) == 0:
        assert n_zeilen_initial == len(df)
        return df

    # Versuch 3: Bei weiteren Unbekannten muss Ortsname ohne ", Stadt"-Suffix übereinstimmen,
    # PLZ wird ignoriert. Beachte nur Gemeindeverz.-Einträge mit plz_eindeutig=False
    vz_uneind_plz = gem_vz[gem_vz.plz_eindeutig == False].copy()
    vz_uneind_plz['ort'] = vz_uneind_plz['gemeinde_bez'].apply(ort_ohne_suffix)
    orte_reg_schluessel3 = vz_uneind_plz.loc[vz_uneind_plz.ort.isin(set(unbekannte[spalte_ort])),
                                             [gem_vz_reg_schluessel, 'ort']]
    
    if len(orte_reg_schluessel3) > 0:
        tmp = pd.merge(pd.DataFrame(unbekannte[spalte_ort]), orte_reg_schluessel3,
                       how='left',
                       left_on=[spalte_ort],
                       right_on=['ort'])[gem_vz_reg_schluessel]
        tmp.name = spalte_reg_schluessel
        tmp.index = unbekannte.index
        df.update(tmp)

    assert n_zeilen_initial == len(df)
    return df


#%%


def _gemeindedatenzeilen(datei, encoding, satzart):
    satzart = set(map(str, satzart))
    gemeindedaten = StringIO()
    with open(datei, encoding=encoding) as f:
        for line in f:
            if len(line) >= 2:
                l_start = line[:2]
                if l_start in satzart:
                    gemeindedaten.write(line)
    
    gemeindedaten.seek(0)   # reset to start
    
    return gemeindedaten


def _gemeindedaten_tabelle(zeilen_buf, spalten_breite, spalten_typ, stand_spalte_idx):
    nichtleer = [i for i, s in enumerate(spalten_breite.keys()) if 'leer_' not in s]
    return pd.read_fwf(zeilen_buf,
                       widths=spalten_breite.values(),
                       header=None,
                       names=spalten_breite.keys(),
                       usecols=nichtleer,
                       converters=spalten_typ,
                       parse_dates=stand_spalte_idx)   # "stand" spalte


def _zu_int_var(ser):
    return ser.fillna(-1).astype(int)
