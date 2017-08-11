# Gemeindeverzeichnis

August 2017, Markus Konrad <markus.konrad@wzb.eu> / [Wissenschaftszentrum Berlin für Sozialforschung](https://www.wzb.eu/en)

## Python-Modul zum Einlesen von Gemeindeverzeichnisdaten des Statistischen Bundesamts

Die Gemeindeverzeichnisdaten werden als [pandas](http://pandas.pydata.org/) DataFrame zur weiteren Verarbeitung in Python eingelesen.

Die Daten müssen als GV100 im ASCII-Format vorliegen. Download der Daten unter: https://www.destatis.de/DE/ZahlenFakten/LaenderRegionen/Regionales/Gemeindeverzeichnis/Gemeindeverzeichnis.html

### Einlesen der Gemeindeverzeichnisdaten

```
import gemeindeverz

gemvz = gemeindeverz.einlesen('GV100AD_31032016.ASC')

gemvz.sample(5)
```

```
       satzart                          stand reg_schluessel  gemeinde_verb  \
10413       60  2016-03-31T00:00:00.000000000       16062036           5006   
10116       60  2016-03-31T00:00:00.000000000       15082301            301   
584         60  2016-03-31T00:00:00.000000000       01058033           5889   
9426        60  2016-03-31T00:00:00.000000000       13075050           5555   
3770        60  2016-03-31T00:00:00.000000000       07141054           5005   

                gemeinde_bez  schluesselfelder  flaeche_ha  bevoelkerung_ges  \
10413          Neustadt/Harz                64        1147              1110   
10116  Raguhn-Jeßnitz, Stadt                63        9713              9540   
584                   Brügge                64         786              1025   
9426           Hinrichshagen                64         998               816   
3770                  Herold                64         409               423   

       bevoelkerung_maennl    plz  plz_eindeutig finanzamts_bezirk  \
10413                  569  99762          False              4159   
10116                 4748  06779          False              3116   
584                    533  24582           True              2124   
9426                   419  17498           True              4084   
3770                   208  56368           True              2730   

      gerichtsbarkeit arbeitsagentur_bezirk bundestagswahlkreise_von  \
10413            1405                 09701                      189   
10116            1302                 04203                       71   
584              1524                 13901                        4   
9426             1403                 03001                       15   
3770             2208                 53509                      205   

      bundestagswahlkreise_bis bemerkungen  
10413                      NaN         NaN  
10116                      NaN         NaN  
584                        NaN         NaN  
9426                       NaN         NaN  
3770                       NaN         NaN
```

### Ermitteln von Regionalschlüsseln

```
orte = pd.DataFrame({'ort': ['Raguhn-Jeßnitz', 'Brügge'], 'plz': ['06779', '24582']})
orte
```

```
              ort    plz
0  Raguhn-Jeßnitz  06779
1          Brügge  24582
```

```
gemeindeverz.reg_schluessel_ermitteln(gemvz, orte, 'plz', 'ort', 'reg_schluessel')
```

```
              ort    plz reg_schluessel
0  Raguhn-Jeßnitz  06779       15082301
1          Brügge  24582       01058033
```