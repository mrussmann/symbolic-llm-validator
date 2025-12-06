# Logic-Guard-Layer: Schulungsunterlagen

**Neuro-symbolische Hybrid-Architektur zur Validierung von KI-Outputs**

*Fachliche Grundlagen für Entwickler und technische Mitarbeiter*

---

## Inhaltsverzeichnis

1. [Modul 1: Das Problem verstehen](#modul-1-das-problem-verstehen)
2. [Modul 2: Der Lösungsansatz](#modul-2-der-lösungsansatz)
3. [Modul 3: Ontologien verstehen](#modul-3-ontologien-verstehen)
4. [Modul 4: Die vier Kernkomponenten](#modul-4-die-vier-kernkomponenten)
5. [Modul 5: Technische Risiken](#modul-5-technische-risiken)
6. [Modul 6: Architekturentscheidungen](#modul-6-architekturentscheidungen)
7. [Modul 7: Synthese und Ausblick](#modul-7-synthese-und-ausblick)

---

# Modul 1: Das Problem verstehen

**Lernziele:** Nach diesem Modul verstehst du, warum Large Language Models trotz ihrer beeindruckenden Fähigkeiten für technische Anwendungen nicht ohne weiteres einsetzbar sind und welche Fehlerarten auftreten können.

**Geschätzte Dauer:** 2 Stunden

---

## 1.1 Was sind Large Language Models?

Large Language Models (LLMs) wie GPT-4, Claude oder Llama sind neuronale Netzwerke, die auf riesigen Textmengen trainiert wurden. Sie haben die Fähigkeit, menschenähnliche Texte zu generieren, Fragen zu beantworten, Code zu schreiben und komplexe Aufgaben zu lösen.

### Wie funktionieren LLMs?

LLMs arbeiten nach dem Prinzip der **Token-Vorhersage**. Sie berechnen für jedes mögliche nächste Wort (Token) eine Wahrscheinlichkeit und wählen dann – vereinfacht gesagt – das wahrscheinlichste aus.

Mathematisch ausgedrückt:

```
P(nächstes_token | alle_bisherigen_tokens)
```

Das Modell optimiert auf **sprachliche Kohärenz**: Der generierte Text soll grammatikalisch korrekt und stilistisch passend sein. Das Modell optimiert jedoch **nicht** auf faktische Korrektheit.

### Ein wichtiges Missverständnis

Viele Menschen glauben, LLMs würden "verstehen", was sie schreiben. Das ist nicht der Fall. Ein LLM hat kein Modell der Welt, keine Vorstellung von Physik, keine Kenntnis von Kausalzusammenhängen. Es erkennt statistische Muster in Texten und reproduziert diese.

**Beispiel:** Ein LLM kann den Satz "Wasser kocht bei 100°C" korrekt wiedergeben, weil dieser Satz häufig in den Trainingsdaten vorkommt. Es "versteht" aber nicht, warum das so ist oder was passiert, wenn der Luftdruck sich ändert.

---

## 1.2 Das Phänomen der Halluzination

### Definition

> **Halluzination:** Eine Halluzination in LLMs bezeichnet die Generierung von Outputs, die (a) faktisch inkorrekt sind, (b) logisch inkonsistent mit dem Kontext sind, oder (c) physikalisch unmögliche Zustände beschreiben, obwohl sie sprachlich kohärent erscheinen.

### Warum halluzinieren LLMs?

Die Ursache liegt in der Architektur:

1. **Keine Faktendatenbank:** Das Modell speichert keine Fakten als solche, sondern statistische Zusammenhänge zwischen Wörtern.

2. **Keine Unsicherheitsanzeige:** Das Modell kann nicht sagen "Das weiß ich nicht". Es generiert immer eine Antwort.

3. **Hohe Konfidenz bei Fehlern:** Das Modell zeigt oft die gleiche sprachliche Sicherheit bei richtigen und falschen Aussagen.

4. **Keine logische Prüfung:** Das Modell prüft nicht, ob seine Aussagen widerspruchsfrei sind.

### Beispiele für Halluzinationen

**Beispiel 1: Erfundene Fakten**
```
Frage: "Wer hat 1987 den Nobelpreis für Literatur gewonnen?"
LLM: "Der Nobelpreis für Literatur 1987 ging an Gabriel García Márquez 
      für sein Lebenswerk."

Realität: Márquez erhielt den Preis 1982. 1987 gewann Joseph Brodsky.
```

**Beispiel 2: Physikalische Unmöglichkeit**
```
Frage: "Wie lange hält ein Hydraulikschlauch bei 500 bar Dauerdruck?"
LLM: "Bei sachgemäßer Verwendung kann ein Standard-Hydraulikschlauch 
      bei 500 bar Dauerdruck etwa 10.000 Betriebsstunden erreichen."

Problem: Standard-Hydraulikschläuche sind für maximal 350 bar ausgelegt.
         500 bar würde zum sofortigen Versagen führen.
```

**Beispiel 3: Logische Inkonsistenz**
```
LLM-Output in einem Wartungsprotokoll:
"Die Pumpe wurde am 15.03.2024 ausgetauscht, nachdem sie am 20.03.2024 
ausgefallen war."

Problem: Die Reparatur kann nicht vor dem Ausfall stattgefunden haben.
```

---

## 1.3 Warum ist das in technischen Domänen kritisch?

In vielen Anwendungsbereichen sind Fehler tolerierbar oder leicht zu erkennen. Wenn ein LLM einen kreativen Text schreibt und dabei einen historischen Fehler macht, ist das ärgerlich, aber nicht gefährlich.

In technischen Domänen sieht das anders aus:

### Sicherheitskritische Anwendungen

**Wartung und Instandhaltung:** Falsche Wartungsintervalle können zu Ausfällen oder Unfällen führen.

**Medizin:** Falsche Dosierungsangaben oder Wechselwirkungen können Patienten gefährden.

**Recht:** Falsche Gesetzesverweise können zu fehlerhaften Entscheidungen führen.

**Finanzen:** Falsche Berechnungen können erhebliche finanzielle Schäden verursachen.

### Das Vertrauensproblem

Der Mensch neigt dazu, sprachlich kohärenten Texten zu vertrauen. Ein technischer Bericht, der professionell formuliert ist, wird eher akzeptiert – auch wenn er Fehler enthält. LLMs produzieren genau solche professionell klingenden Texte, können aber die Korrektheit nicht garantieren.

---

## 1.4 Warum RAG das Problem nicht löst

### Was ist RAG?

**Retrieval-Augmented Generation (RAG)** ist ein Ansatz, der LLMs mit einer Retrieval-Komponente ergänzt. Bevor das LLM antwortet, werden relevante Dokumente aus einer Wissensbasis abgerufen und dem Modell als Kontext mitgegeben.

```
Ablauf:
1. Nutzer stellt Frage
2. System sucht relevante Dokumente
3. Dokumente werden dem LLM als Kontext übergeben
4. LLM generiert Antwort basierend auf Dokumenten
```

### Die Grenzen von RAG

RAG verbessert die faktische Grundierung, löst aber das Validierungsproblem nicht:

**Problem 1: Keine Konsistenzprüfung**
RAG stellt keine logische Konsistenz zwischen verschiedenen abgerufenen Fakten sicher. Das LLM kann widersprüchliche Informationen aus verschiedenen Dokumenten kombinieren.

**Problem 2: Weiterhin Halluzinationen möglich**
Das LLM kann Informationen halluzinieren, die nicht in den abgerufenen Dokumenten stehen. Es "erfindet" Details, die plausibel klingen.

**Problem 3: Keine Plausibilitätsprüfung**
RAG prüft nicht, ob die generierte Antwort physikalisch oder logisch möglich ist. Es gibt keinen Mechanismus, der sagt: "Diese Aussage widerspricht einem Naturgesetz."

### Beispiel: RAG-Versagen

```
Abgerufene Dokumente:
- Dokument A: "Motor Typ X hat eine maximale Lebensdauer von 20.000 Stunden"
- Dokument B: "Empfohlenes Wartungsintervall für Industriemotoren: 5.000 Stunden"

LLM-Antwort:
"Für Motor Typ X empfehlen wir ein Wartungsintervall von 25.000 Stunden."

Problem: Das LLM hat die Zahlen falsch kombiniert. Das Intervall übersteigt 
die Lebensdauer – ein logischer Widerspruch, den RAG nicht erkennt.
```

---

## 1.5 Zusammenfassung Modul 1

### Kernaussagen

1. **LLMs optimieren auf Sprache, nicht auf Wahrheit.** Sie generieren statistisch wahrscheinliche Texte, keine garantiert korrekten Fakten.

2. **Halluzinationen sind systemimmanent.** Sie sind kein Bug, der gefixt werden kann, sondern eine Eigenschaft der Architektur.

3. **In technischen Domänen sind Fehler inakzeptabel.** Falsche Wartungsintervalle, Dosierungen oder Berechnungen können gefährlich sein.

4. **RAG verbessert, löst aber nicht.** Auch mit Retrieval kann das LLM inkonsistente oder physikalisch unmögliche Aussagen generieren.

### Die zentrale Frage

> Wie können wir die sprachlichen Fähigkeiten von LLMs nutzen, ohne ihre Unzuverlässigkeit in Kauf nehmen zu müssen?

Diese Frage führt uns zu Modul 2: dem Lösungsansatz der neuro-symbolischen Hybrid-Architektur.

---

## Übung 1: Halluzinationen erkennen

**Aufgabe:** Analysiere die folgenden LLM-Outputs und identifiziere die Fehlerart.

**Text 1:**
```
"Der Ölwechsel am Kompressor K-101 wurde durchgeführt. Verwendet wurde 
SAE 30 Motoröl, 15 Liter. Der Kompressor hat jetzt 45.000 Betriebsstunden 
und wurde auf das nächste Wartungsintervall bei 50.000 Stunden eingestellt."
```

**Fragen:**
- Welche Informationen sind extrahierbar?
- Welche Informationen müssten geprüft werden?
- Welche möglichen Fehler könnten enthalten sein?

**Text 2:**
```
"Die Hydraulikpumpe zeigt einen Druck von -5 bar an. Dies deutet auf 
ein Leck in der Saugleitung hin. Empfohlene Maßnahme: Druck auf 
Normalwert von 200 bar erhöhen."
```

**Fragen:**
- Welcher physikalische Fehler ist enthalten?
- Ist die empfohlene Maßnahme sinnvoll?

---

# Modul 2: Der Lösungsansatz

**Lernziele:** Nach diesem Modul verstehst du das Konzept der neuro-symbolischen KI, wie symbolische Logik als "Wächter" über neuronale Netze fungieren kann und wie die Logic-Guard-Layer-Architektur aufgebaut ist.

**Geschätzte Dauer:** 2 Stunden

---

## 2.1 Zwei Paradigmen der künstlichen Intelligenz

Die Geschichte der KI kennt zwei grundlegende Ansätze, die lange als gegensätzlich galten:

### Symbolische KI (1950er-1980er)

Die frühe KI-Forschung setzte auf **explizite Wissensrepräsentation**. Wissen wurde in Form von Regeln, Logik und Symbolen kodiert.

**Merkmale:**
- Explizite Regeln: "WENN Temperatur > 100 UND Druck > 10 DANN Alarm"
- Nachvollziehbare Entscheidungen
- Deterministisch: Gleiche Eingabe → Gleiche Ausgabe
- Erfordert manuelle Wissensmodellierung

**Stärken:**
- Zuverlässig und vorhersagbar
- Erklärbare Entscheidungen
- Garantierte Einhaltung von Regeln

**Schwächen:**
- Schwierig, alles Wissen manuell zu kodieren
- Unflexibel bei unvorhergesehenen Situationen
- Kann nicht mit unstrukturierten Daten (Text, Bilder) umgehen

### Neuronale KI (1980er-heute)

Der moderne KI-Boom basiert auf **statistischem Lernen**. Neuronale Netze lernen Muster aus Daten, ohne dass Regeln explizit programmiert werden.

**Merkmale:**
- Lernt aus Beispielen
- Implizites Wissen in Gewichten des Netzwerks
- Probabilistisch: Ausgabe basiert auf Wahrscheinlichkeiten
- Skaliert mit Datenmenge und Rechenleistung

**Stärken:**
- Flexibel und anpassungsfähig
- Kann mit unstrukturierten Daten umgehen
- Lernt automatisch aus Daten

**Schwächen:**
- "Black Box": Entscheidungen schwer nachvollziehbar
- Keine Garantien für Korrektheit
- Kann halluzinieren

### Vergleichstabelle

| Eigenschaft | Symbolische KI | Neuronale KI |
|-------------|----------------|--------------|
| Wissensrepräsentation | Explizit (Regeln) | Implizit (Gewichte) |
| Lernfähigkeit | Gering | Hoch |
| Erklärbarkeit | Hoch | Gering |
| Zuverlässigkeit | Hoch (wenn Regeln vollständig) | Variabel |
| Flexibilität | Gering | Hoch |
| Umgang mit Text | Schwach | Stark |

---

## 2.2 Die neuro-symbolische Synthese

### Die Grundidee

Warum nicht beide Ansätze kombinieren? Die Idee der **neuro-symbolischen KI** ist, die Stärken beider Paradigmen zu vereinen:

- **Neuronale Komponente:** Verarbeitet unstrukturierte Daten, versteht Sprache, ist flexibel
- **Symbolische Komponente:** Prüft Ergebnisse gegen Regeln, garantiert Konsistenz, ist erklärbar

### Drei Integrationsstrategien

Es gibt verschiedene Wege, neuronale und symbolische Systeme zu kombinieren:

**1. Symbolik in Neuronalem**
Symbolisches Wissen wird in das Training des neuronalen Netzes einbezogen. Das Netz lernt, Regeln zu befolgen.

*Problem:* Erfordert Neutraining, keine harten Garantien

**2. Neuronales in Symbolik**
Neuronale Netze werden als Komponenten in einem symbolischen System eingesetzt, z.B. für Spracherkennung.

*Problem:* Begrenzte Flexibilität

**3. Neuronalem mit symbolischer Validierung (unser Ansatz)**
Das neuronale System generiert Outputs, die anschließend von einem symbolischen System validiert werden.

*Vorteil:* Keine Modifikation des LLM nötig, harte Garantien möglich

---

## 2.3 Logic-Guard-Layer: Das Konzept

### Die Architekturidee

Logic-Guard-Layer implementiert die dritte Strategie: **Post-hoc-Validierung**. Das System positioniert sich als Middleware zwischen LLM und Endanwendung.

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
│             │     │   Logic-Guard-Layer │     │             │
│    LLM      │────▶│   (Validierung)     │────▶│  Anwendung  │
│             │     │                     │     │             │
└─────────────┘     └─────────────────────┘     └─────────────┘
                              │
                              │ Feedback bei Fehler
                              │
                              ▼
                    ┌─────────────────────┐
                    │     Ontologie /     │
                    │    Wissensgraph     │
                    └─────────────────────┘
```

### Kernprinzip

> **Symbolische KI überwacht neuronale KI.** Nur Outputs, die alle definierten Regeln erfüllen, werden an nachgelagerte Systeme weitergegeben.

### Was wird validiert?

1. **Typkorrektheit:** Ist die genannte Entität vom richtigen Typ?
2. **Wertebereiche:** Liegen numerische Werte in plausiblen Grenzen?
3. **Relationen:** Sind angegebene Beziehungen zulässig?
4. **Logische Konsistenz:** Widersprechen sich Aussagen?
5. **Physikalische Plausibilität:** Sind die Aussagen physikalisch möglich?

---

## 2.4 Die vier Kernkomponenten

Das Logic-Guard-Layer-System besteht aus vier Hauptkomponenten, die zusammenspielen:

### Komponente 1: Semantischer Parser

**Aufgabe:** Transformiert unstrukturierten Text in maschinenlesbare Datenobjekte.

**Eingabe:** Natürlichsprachlicher Text
**Ausgabe:** Strukturierte Daten (JSON/RDF)

**Beispiel:**
```
Eingabe: "Der Motor M1 hat 15.000 Betriebsstunden und wurde zuletzt 
          am 12.03.2024 gewartet."

Ausgabe: {
  "entität": "Motor",
  "bezeichnung": "M1",
  "betriebsstunden": 15000,
  "letzte_wartung": "2024-03-12"
}
```

### Komponente 2: Ontologie / Wissensgraph

**Aufgabe:** Definiert das "Weltwissen" der Domäne – Konzepte, Relationen und Regeln.

**Inhalt:**
- Welche Konzepte existieren? (Motor, Pumpe, Wartungsintervall)
- Wie hängen sie zusammen? (Motor hatWartungsintervall)
- Welche Regeln gelten? (Wartungsintervall ≤ Lebensdauer)

### Komponente 3: Reasoning-Modul

**Aufgabe:** Prüft, ob die extrahierten Daten mit der Ontologie konsistent sind.

**Eingabe:** Strukturierte Daten vom Parser
**Ausgabe:** Konsistent (ja/nein) + Liste der Verletzungen

**Beispiel:**
```
Eingabe: { "wartungsintervall": 50000, "max_lebensdauer": 20000 }
Regel: wartungsintervall ≤ max_lebensdauer

Ausgabe: {
  "konsistent": false,
  "verletzungen": [
    {
      "regel": "wartungsintervall ≤ max_lebensdauer",
      "nachricht": "Wartungsintervall (50.000) übersteigt Lebensdauer (20.000)"
    }
  ]
}
```

### Komponente 4: Self-Correction Loop

**Aufgabe:** Meldet erkannte Fehler an das LLM zurück und fordert eine korrigierte Antwort an.

**Ablauf:**
1. Fehler erkannt
2. Korrektur-Prompt generieren
3. LLM um Korrektur bitten
4. Korrigierte Antwort erneut validieren
5. Wiederholen bis konsistent oder max. Iterationen erreicht

---

## 2.5 Der Validierungsprozess im Überblick

Der vollständige Ablauf einer Validierung:

```
┌──────────────────────────────────────────────────────────────────┐
│                    VALIDIERUNGSPROZESS                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. EINGABE                                                      │
│     Unstrukturierter Text vom LLM                                │
│     ↓                                                            │
│  2. PARSING                                                      │
│     Extraktion strukturierter Daten                              │
│     ↓                                                            │
│  3. VALIDIERUNG                                                  │
│     Prüfung gegen Ontologie-Axiome                               │
│     ↓                                                            │
│  4. ENTSCHEIDUNG                                                 │
│     ┌─────────────┬─────────────┐                                │
│     │ Konsistent  │ Inkonsistent│                                │
│     │      ↓      │      ↓      │                                │
│     │   AUSGABE   │  KORREKTUR  │                                │
│     │             │      ↓      │                                │
│     │             │ Zurück zu 1 │                                │
│     └─────────────┴─────────────┘                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2.6 Warum dieser Ansatz funktioniert

### Vorteile der Post-hoc-Validierung

1. **Kein LLM-Training nötig:** Das LLM bleibt unverändert. Es kann jedes beliebige Modell verwendet werden.

2. **Harte Garantien:** Die symbolische Komponente prüft deterministisch. Wenn eine Regel verletzt ist, wird sie erkannt.

3. **Erklärbarkeit:** Bei einer Ablehnung kann genau angegeben werden, welche Regel verletzt wurde.

4. **Modularität:** Die Ontologie kann unabhängig vom Rest des Systems angepasst werden.

5. **Domänenunabhängigkeit:** Die Architektur ist generisch. Nur die Ontologie ist domänenspezifisch.

### Was der Ansatz nicht kann

1. **Keine 100% Vollständigkeit:** Die Validierung ist nur so gut wie die Ontologie. Nicht modellierte Fehlerarten werden nicht erkannt.

2. **Erhöhte Latenz:** Die zusätzliche Validierung kostet Zeit.

3. **Ontologie-Aufwand:** Das Erstellen einer guten Ontologie erfordert Domänenwissen und Aufwand.

---

## 2.7 Zusammenfassung Modul 2

### Kernaussagen

1. **Zwei KI-Paradigmen ergänzen sich.** Neuronale KI ist flexibel aber unzuverlässig, symbolische KI ist zuverlässig aber unflexibel.

2. **Logic-Guard-Layer kombiniert beide.** Das LLM generiert, die Ontologie validiert.

3. **Post-hoc-Validierung ermöglicht harte Garantien.** Nur geprüfte Outputs werden weitergegeben.

4. **Vier Komponenten arbeiten zusammen:** Parser, Ontologie, Reasoner, Correction Loop.

### Die Leitfrage für die nächsten Module

> Wie implementiert man die einzelnen Komponenten? Was sind die technischen Herausforderungen?

---

## Übung 2: Validierungslogik verstehen

**Aufgabe:** Gegeben ist folgender LLM-Output und eine vereinfachte Ontologie. Bestimme, ob der Output konsistent ist.

**LLM-Output:**
```
{
  "komponente": "Hydraulikpumpe",
  "betriebsstunden": 8500,
  "wartungsintervall": 5000,
  "max_lebensdauer": 10000,
  "druck_bar": 280
}
```

**Ontologie-Regeln:**
```
R1: wartungsintervall ≤ max_lebensdauer
R2: betriebsstunden ≤ max_lebensdauer
R3: 0 < druck_bar ≤ 350
R4: betriebsstunden ist ganzzahlig und ≥ 0
```

**Fragen:**
1. Welche Regeln sind erfüllt?
2. Welche Regeln sind verletzt?
3. Wie würde ein Korrektur-Prompt aussehen?

---

# Modul 3: Ontologien verstehen

**Lernziele:** Nach diesem Modul verstehst du, was eine Ontologie ist, wie sie aufgebaut ist, welche Arten von Constraints definiert werden können und wie der Unterschied zwischen Ontologie und Knowledge Graph ist.

**Geschätzte Dauer:** 4 Stunden

---

## 3.1 Was ist eine Ontologie?

### Definition

> **Ontologie (in der Informatik):** Eine formale, explizite Spezifikation einer Konzeptualisierung. Sie definiert die Begriffe einer Domäne und die Beziehungen zwischen ihnen.

Einfacher gesagt: Eine Ontologie ist ein **formales Modell des Wissens** über einen Bereich. Sie legt fest:
- Welche Dinge existieren (Konzepte/Klassen)
- Wie diese Dinge zusammenhängen (Relationen)
- Welche Eigenschaften sie haben (Attribute)
- Welche Regeln gelten (Axiome)

### Woher kommt der Begriff?

Der Begriff "Ontologie" stammt aus der Philosophie und bedeutet dort "Lehre vom Sein". In der Informatik wurde er übernommen, um formale Wissensmodelle zu bezeichnen.

### Warum brauchen wir Ontologien?

Ontologien ermöglichen es, Wissen so zu formalisieren, dass Maschinen damit arbeiten können. Im Kontext des Logic-Guard-Layer:

- **Ohne Ontologie:** Das System weiß nicht, was "Motor" oder "Wartungsintervall" bedeutet
- **Mit Ontologie:** Das System kennt die Konzepte, ihre Eigenschaften und die geltenden Regeln

---

## 3.2 Die Bausteine einer Ontologie

Eine Ontologie besteht aus vier grundlegenden Bausteinen:

### 3.2.1 Konzepte (Klassen)

Konzepte beschreiben **Kategorien von Dingen**, die in der Domäne existieren. Sie bilden typischerweise eine Hierarchie.

**Beispiel: Technische Wartungsdomäne**
```
Komponente (Oberklasse)
├── Motor
│   ├── Elektromotor
│   └── Verbrennungsmotor
├── Pumpe
│   ├── Hydraulikpumpe
│   └── Vakuumpumpe
└── Ventil
    ├── Regelventil
    └── Absperrventil
```

**Eigenschaften von Klassen:**
- **Vererbung:** Unterklassen erben Eigenschaften der Oberklasse
- **Disjunktheit:** Klassen können als gegenseitig ausschließend definiert werden (ein Ding kann nicht beides sein)
- **Äquivalenz:** Zwei Klassen können als bedeutungsgleich definiert werden

### 3.2.2 Relationen (Properties)

Relationen beschreiben **Beziehungen zwischen Konzepten**. Es gibt zwei Arten:

**Object Properties:** Beziehungen zwischen Instanzen
```
hatKomponente: Anlage → Komponente
istTeilVon: Komponente → Baugruppe
wirdGewartetVon: Komponente → Techniker
```

**Datatype Properties:** Beziehungen zu Datenwerten
```
hatBetriebsstunden: Komponente → Integer
hatSeriennummer: Komponente → String
hatLetzeWartung: Komponente → Date
```

**Eigenschaften von Relationen:**
- **Domain:** Welche Klasse kann diese Relation haben?
- **Range:** Welche Klasse/welcher Datentyp ist das Ziel?
- **Kardinalität:** Wie viele Beziehungen sind erlaubt?
- **Transitivität:** Wenn A→B und B→C, gilt dann A→C?
- **Symmetrie:** Wenn A→B, gilt dann auch B→A?

### 3.2.3 Axiome (Regeln)

Axiome sind **logische Aussagen**, die immer gelten müssen. Sie definieren Constraints, gegen die validiert wird.

**Beispiele:**

**Subklassen-Axiom:**
```
Elektromotor ⊆ Motor
(Jeder Elektromotor ist ein Motor)
```

**Äquivalenz-Axiom:**
```
DefekteKomponente ≡ Komponente ∧ hatStatus("defekt")
(Eine defekte Komponente ist eine Komponente mit Status "defekt")
```

**Wertebereichs-Axiom:**
```
∀x: hatBetriebsstunden(x, v) → v ≥ 0
(Betriebsstunden können nicht negativ sein)
```

**Relationales Axiom:**
```
∀x: hatWartungsintervall(x, w) ∧ hatLebensdauer(x, l) → w ≤ l
(Wartungsintervall darf Lebensdauer nicht übersteigen)
```

### 3.2.4 Instanzen (Individuen)

Instanzen sind **konkrete Objekte** der Domäne – die tatsächlichen Daten.

**Beispiel:**
```
Motor_M1:
  - Typ: Elektromotor
  - Seriennummer: "EM-2024-001"
  - Betriebsstunden: 15000
  - Max. Lebensdauer: 50000
  - Wartungsintervall: 5000
```

---

## 3.3 TBox und ABox

In der Beschreibungslogik unterscheidet man zwei "Boxen":

### TBox (Terminological Box)

Die TBox enthält das **Schema** – die Definition von Konzepten, Relationen und Axiomen. Sie beschreibt, was es in der Domäne *geben kann*.

```
TBox-Beispiel:
- Motor ist eine Unterklasse von Komponente
- Jede Komponente hat genau eine Seriennummer
- Wartungsintervall muss kleiner als Lebensdauer sein
```

### ABox (Assertional Box)

Die ABox enthält die **Instanzdaten** – konkrete Fakten über die Welt. Sie beschreibt, was es *tatsächlich gibt*.

```
ABox-Beispiel:
- Motor_M1 ist ein Motor
- Motor_M1 hat Seriennummer "EM-2024-001"
- Motor_M1 hat 15000 Betriebsstunden
```

### Zusammenspiel

Das Reasoning prüft, ob die ABox (Daten) mit der TBox (Regeln) konsistent ist:

```
TBox-Regel: Wartungsintervall ≤ Lebensdauer
ABox-Fakt: Motor_M1 hat Wartungsintervall 60000
ABox-Fakt: Motor_M1 hat Lebensdauer 50000

→ Inkonsistenz erkannt!
```

---

## 3.4 Ontologie vs. Knowledge Graph

Diese Begriffe werden oft synonym verwendet, bezeichnen aber unterschiedliche Konzepte:

### Ontologie (nur TBox)

Eine reine Ontologie enthält nur das Schema – keine Instanzdaten. Sie definiert, *was* es geben kann und welche Regeln gelten.

**Geeignet für:** Strukturvalidierung, Schema-Prüfung

### Knowledge Graph (TBox + ABox)

Ein Knowledge Graph erweitert die Ontologie um konkrete Instanzdaten. Er enthält sowohl das Schema als auch die Fakten.

**Geeignet für:** Faktenprüfung, Referenzierung, Abfragen

### Wann brauche ich was?

| Anforderung | Nur Ontologie | Knowledge Graph |
|-------------|---------------|-----------------|
| "Ist der Wert im gültigen Bereich?" | ✓ | ✓ |
| "Ist diese Komponente vom Typ Motor?" | ✓ | ✓ |
| "Existiert Motor M1 tatsächlich?" | ✗ | ✓ |
| "Welche Komponenten gehören zu Anlage A?" | ✗ | ✓ |
| "Hat dieser Techniker die Berechtigung?" | ✗ | ✓ |

**Empfehlung für Logic-Guard-Layer:**
- **Prototyp:** Starte mit einer reinen Ontologie (Schema-Validierung)
- **Später:** Ergänze Instanzdaten, wenn Faktenprüfung nötig wird

---

## 3.5 OWL als Ontologiesprache

### Was ist OWL?

**OWL (Web Ontology Language)** ist der W3C-Standard für Ontologien im Semantic Web. Es gibt verschiedene Varianten:

- **OWL Lite:** Eingeschränkt, schnelles Reasoning
- **OWL DL:** Beschreibungslogik, gute Balance
- **OWL Full:** Maximale Ausdrucksstärke, aber nicht entscheidbar

Für Logic-Guard-Layer empfehlen wir **OWL 2 DL**, da es einen guten Kompromiss zwischen Ausdrucksstärke und Entscheidbarkeit bietet.

### Die zugrundeliegende Logik: SROIQ(D)

OWL 2 DL basiert auf der Beschreibungslogik SROIQ(D). Die Buchstaben stehen für unterstützte Features:

- **S:** Basis (ALC) + Transitivität
- **R:** Role Hierarchies, Role Chains
- **O:** Nominals (Aufzählungsklassen)
- **I:** Inverse Roles
- **Q:** Qualified Cardinality Restrictions
- **D:** Datatypes (Zahlen, Strings, etc.)

### OWL-Syntax-Beispiel

```xml
<!-- Klasse definieren -->
<owl:Class rdf:about="#Motor">
    <rdfs:subClassOf rdf:resource="#Komponente"/>
</owl:Class>

<!-- Property definieren -->
<owl:DatatypeProperty rdf:about="#hatBetriebsstunden">
    <rdfs:domain rdf:resource="#Komponente"/>
    <rdfs:range rdf:resource="xsd:integer"/>
</owl:DatatypeProperty>

<!-- Constraint definieren: Betriebsstunden ≥ 0 -->
<owl:Restriction>
    <owl:onProperty rdf:resource="#hatBetriebsstunden"/>
    <owl:someValuesFrom>
        <rdfs:Datatype>
            <owl:onDatatype rdf:resource="xsd:integer"/>
            <owl:withRestrictions>
                <rdf:List>
                    <rdf:first>
                        <xsd:minInclusive rdf:datatype="xsd:integer">0</xsd:minInclusive>
                    </rdf:first>
                </rdf:List>
            </owl:withRestrictions>
        </rdfs:Datatype>
    </owl:someValuesFrom>
</owl:Restriction>
```

---

## 3.6 Constraint-Typen im Detail

Für den Logic-Guard-Layer unterscheiden wir fünf Kategorien von Constraints:

### 3.6.1 Typ-Constraints

**Frage:** Gehört eine Entität zur richtigen Klasse?

**Beispiele:**
- Motor_M1 ist ein Motor (nicht eine Pumpe)
- Der genannte Wert ist eine Temperatur (nicht ein Druck)

**OWL-Umsetzung:** Klasseninstanziierung, disjunkte Klassen

### 3.6.2 Wertebereichs-Constraints

**Frage:** Liegt ein numerischer Wert im gültigen Bereich?

**Beispiele:**
- Druck zwischen 0 und 350 bar
- Temperatur zwischen -40°C und +150°C
- Betriebsstunden ≥ 0

**OWL-Umsetzung:** Datatype Restrictions (minInclusive, maxInclusive)

### 3.6.3 Relationale Constraints

**Frage:** Sind Beziehungen zwischen Entitäten gültig?

**Beispiele:**
- Eine Komponente kann nur Teil einer existierenden Anlage sein
- Ein Wartungsereignis muss genau einen Techniker haben
- Wartungsintervall ≤ maximale Lebensdauer

**OWL-Umsetzung:** Property Restrictions, Cardinality Constraints

### 3.6.4 Temporale Constraints

**Frage:** Sind zeitliche Abhängigkeiten korrekt?

**Beispiele:**
- Wartungsdatum muss vor dem aktuellen Datum liegen
- Reparatur kann nicht vor dem Ausfall stattfinden
- Inbetriebnahme muss vor erster Wartung liegen

**OWL-Umsetzung:** Datentyp-Vergleiche, SWRL-Regeln

### 3.6.5 Physikalische Constraints

**Frage:** Werden Naturgesetze eingehalten?

**Beispiele:**
- Keine negativen Betriebsstunden
- Ausgangsdruck ≤ Eingangsdruck (ohne Pumpe)
- Energieerhaltung bei Berechnungen

**OWL-Umsetzung:** Komplexe Datentyp-Restrictions, externe Berechnungsregeln

### Übersichtstabelle

| Typ | Beispiel | Komplexität | OWL-Umsetzung |
|-----|----------|-------------|---------------|
| Typ | Motor ∈ Komponente | Niedrig | Class Assertion |
| Wertebereich | 0 < Druck < 350 | Niedrig | Datatype Restriction |
| Relational | Teil ⊆ Ganzes | Mittel | Property Restriction |
| Temporal | t_Wartung < t_Ausfall | Mittel | SWRL / Custom |
| Physikalisch | E = mc² | Hoch | External Rules |

---

## 3.7 Erstellung einer Ontologie

### Der Prozess

1. **Domänenanalyse**
   - Welche Konzepte sind relevant?
   - Welche Relationen bestehen?
   - Welche Regeln gelten?
   - Interviews mit Domänenexperten

2. **Formalisierung**
   - Übersetzung in OWL-Syntax
   - Definition von Klassen, Properties, Axiomen
   - Tool: Protégé (grafischer Editor)

3. **Validierung**
   - Syntaktische Prüfung (ist das OWL gültig?)
   - Logische Konsistenz (widersprechen sich Regeln?)
   - Semantische Vollständigkeit (sind alle Fälle abgedeckt?)

4. **Iteration**
   - Testen mit Beispieldaten
   - Ergänzen fehlender Regeln
   - Anpassen bei neuen Anforderungen

### Praktische Tipps

**Start klein:** Beginne mit 10-20 Konzepten und den wichtigsten Regeln. Erweitere iterativ.

**Nutze Standards:** Prüfe, ob es für deine Domäne bereits Ontologien gibt (ECLASS, ISO-Standards).

**Dokumentiere:** Jedes Konzept und jede Regel sollte kommentiert sein.

**Teste früh:** Validiere die Ontologie mit echten Testfällen, bevor sie produktiv geht.

---

## 3.8 Zusammenfassung Modul 3

### Kernaussagen

1. **Eine Ontologie ist ein formales Wissensmodell.** Sie definiert Konzepte, Relationen und Regeln einer Domäne.

2. **Vier Bausteine:** Konzepte (Klassen), Relationen (Properties), Axiome (Regeln), Instanzen (Individuen).

3. **TBox vs. ABox:** Das Schema (was kann es geben?) vs. die Daten (was gibt es tatsächlich?).

4. **Fünf Constraint-Typen:** Typ, Wertebereich, Relational, Temporal, Physikalisch.

5. **OWL 2 DL** ist die empfohlene Sprache für Logic-Guard-Layer.

---

## Übung 3: Ontologie-Design

**Aufgabe:** Entwirf eine einfache Ontologie für die Domäne "Fahrzeugwartung".

**Schritt 1:** Identifiziere mindestens 5 Konzepte und ordne sie hierarchisch.

**Schritt 2:** Definiere mindestens 3 Object Properties und 3 Datatype Properties.

**Schritt 3:** Formuliere mindestens 3 Axiome (Regeln), die in dieser Domäne gelten.

**Beispiel-Start:**
```
Konzepte:
- Fahrzeug
  - PKW
  - LKW
- Wartungsereignis
- ...

Properties:
- hatKilometerstand: Fahrzeug → Integer
- ...

Axiome:
- Kilometerstand ≥ 0
- ...
```

---

# Modul 4: Die vier Kernkomponenten

**Lernziele:** Nach diesem Modul verstehst du die technische Funktionsweise jeder Komponente: wie der Parser arbeitet, wie das Reasoning funktioniert und wie der Self-Correction Loop implementiert wird.

**Geschätzte Dauer:** 6 Stunden

---

## 4.1 Semantischer Parser

### 4.1.1 Aufgabe

Der semantische Parser ist die **Brücke zwischen Sprache und Struktur**. Er transformiert unstrukturierten natürlichsprachlichen Text in maschinenlesbare Datenobjekte, die gegen die Ontologie geprüft werden können.

```
Eingabe:  "Der Motor M1 hat 15.000 Betriebsstunden und wurde 
           zuletzt am 12.03.2024 gewartet."

Ausgabe:  {
            "typ": "Wartungsbericht",
            "komponente": {
              "name": "M1",
              "klasse": "Motor",
              "betriebsstunden": 15000
            },
            "wartung": {
              "datum": "2024-03-12"
            }
          }
```

### 4.1.2 Die drei Teilaufgaben

**1. Entity Recognition (Entitätenerkennung)**
Identifiziere domänenrelevante Entitäten im Text.

```
Text: "Der Motor M1 hat 15.000 Betriebsstunden"
       ─────────── 
Entität: Motor M1 (Typ: Komponente)
```

**2. Relation Extraction (Beziehungsextraktion)**
Erkenne Beziehungen zwischen Entitäten.

```
Text: "Motor M1 ist Teil der Anlage A"
       ─────────────────────────────
Relation: (Motor M1) --istTeilVon--> (Anlage A)
```

**3. Slot Filling (Attributzuordnung)**
Ordne Werte den richtigen Attributen zu.

```
Text: "15.000 Betriebsstunden"
       ────────────────────
Attribut: betriebsstunden = 15000
```

### 4.1.3 Hybrid-Ansatz: LLM-gestütztes Parsing

Anstatt einen eigenen Parser von Grund auf zu entwickeln, nutzen wir das LLM selbst für das Parsing – gesteuert durch strukturierte Prompts.

**Schema-Guided Parsing:**

```
Prompt-Vorlage:
═══════════════════════════════════════════════════════════════════
Analysiere den folgenden technischen Text und extrahiere 
strukturierte Informationen gemäß dem Schema:

SCHEMA:
{
  "komponente": {
    "name": "string",
    "typ": "enum[Motor, Pumpe, Ventil, Sensor]",
    "eigenschaften": {
      "betriebsstunden": "integer",
      "wartungsintervall_h": "integer",
      "messwerte": [{"typ": "string", "wert": "float", "einheit": "string"}]
    }
  }
}

TEXT:
{input_text}

Antworte ausschließlich mit validem JSON. Keine Erklärungen.
═══════════════════════════════════════════════════════════════════
```

### 4.1.4 Parsing-Pipeline

Die vollständige Pipeline besteht aus mehreren Schritten:

```
┌─────────────┐
│  Raw Text   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  1. Prompt Generation                   │
│     Schema + Text → Parsing-Prompt      │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  2. LLM Call                            │
│     Prompt → LLM → JSON-String          │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  3. JSON Parsing                        │
│     String → Python Dict                │
│     (Fehlerbehandlung bei ungültigem    │
│      JSON)                              │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  4. Schema Validation                   │
│     Prüfe: Alle Pflichtfelder da?       │
│            Datentypen korrekt?          │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  5. Ontology Mapping                    │
│     JSON → Ontologie-Instanzen          │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Strukturierte Daten für Reasoner       │
└─────────────────────────────────────────┘
```

### 4.1.5 Fehlerbehandlung im Parser

**Syntaktische Fehler:** Das LLM gibt kein valides JSON zurück.
→ Lösung: Retry mit expliziter JSON-Instruktion, ggf. JSON-Reparatur

**Schema-Fehler:** Pflichtfelder fehlen oder haben falsche Typen.
→ Lösung: Gezieltes Nachfragen ("Welchen Typ hat die Komponente?")

**Typ-Fehler:** Wert hat falschen Datentyp (String statt Integer).
→ Lösung: Typ-Coercion versuchen oder Fehler melden

**Konzeptueller Fehler:** Text enthält keine extrahierbaren Informationen.
→ Lösung: Fehler an Aufrufer zurückgeben

### 4.1.6 Pseudocode: Parsing-Algorithmus

```python
def parse(text: str, schema: Schema, ontology: Ontology) -> StructuredData | Error:
    """
    Parst unstrukturierten Text in strukturierte Daten.

    Args:
        text: Der zu parsende Text
        schema: Das erwartete Ausgabeschema
        ontology: Die Domänenontologie

    Returns:
        Strukturierte Daten oder Fehler
    """
    # 1. Prompt generieren
    prompt = generate_parsing_prompt(schema, text)

    # 2. LLM aufrufen
    llm_response = call_llm(prompt, temperature=0)

    # 3. JSON parsen
    try:
        json_data = json.loads(llm_response)
    except JSONDecodeError:
        return Error("PARSE_ERROR", "Ungültiges JSON vom LLM")

    # 4. Schema validieren
    validation_result = validate_schema(json_data, schema)
    if not validation_result.is_valid:
        return Error("SCHEMA_ERROR", validation_result.errors)

    # 5. Auf Ontologie mappen
    structured_data = map_to_ontology(json_data, ontology)

    return structured_data
```

---

## 4.2 Ontologie / Wissensgraph

### 4.2.1 Rolle im System

Die Ontologie ist das **Herzstück des Logic-Guard-Layer**. Sie definiert:
- Was "korrekt" bedeutet
- Welche Constraints gelten
- Wie Entitäten zusammenhängen

Ohne Ontologie gibt es keine Validierung. Ein LLM kann nur validiert werden, wenn die Definition von "korrekt" präzise und vollständig ist.

### 4.2.2 Aufbau für Logic-Guard-Layer

Für unser System strukturieren wir die Ontologie in vier Bereiche:

```
┌─────────────────────────────────────────────────────────────────┐
│                         ONTOLOGIE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   KONZEPTE      │    │   RELATIONEN    │                    │
│  │   (Klassen)     │    │   (Properties)  │                    │
│  │                 │    │                 │                    │
│  │ - Komponente    │    │ - hatStatus     │                    │
│  │ - Motor         │    │ - istTeilVon    │                    │
│  │ - Pumpe         │    │ - hatWartung    │                    │
│  │ - Wartung       │    │ - hatWert       │                    │
│  │ - Messwert      │    │                 │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   AXIOME        │    │   CONSTRAINTS   │                    │
│  │   (Regeln)      │    │   (Prüfregeln)  │                    │
│  │                 │    │                 │                    │
│  │ - Vererbung     │    │ - Wertebereiche │                    │
│  │ - Disjunktheit  │    │ - Kardinalität  │                    │
│  │ - Äquivalenz    │    │ - Custom Rules  │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2.3 Beispiel: Wartungsdomäne

Eine vereinfachte Ontologie für technische Wartung:

**Konzepte:**
```
Komponente
├── RotierendeKomponente
│   ├── Motor
│   └── Pumpe
├── StatischeKomponente
│   ├── Ventil
│   └── Behälter
└── Sensor
    ├── Drucksensor
    └── Temperatursensor

Ereignis
├── Wartungsereignis
├── Ausfallereignis
└── Messereignis
```

**Properties:**
```
Object Properties:
- hatKomponente: Anlage → Komponente
- hatWartung: Komponente → Wartungsereignis
- durchgeführtVon: Wartungsereignis → Techniker

Datatype Properties:
- hatBetriebsstunden: Komponente → xsd:integer
- hatMaxLebensdauer: Komponente → xsd:integer
- hatWartungsintervall: Komponente → xsd:integer
- hatSeriennummer: Komponente → xsd:string
- hatDatum: Ereignis → xsd:date
```

**Axiome (Constraints):**
```
# Wertebereichs-Constraints
C1: hatBetriebsstunden ≥ 0
C2: hatMaxLebensdauer > 0
C3: hatWartungsintervall > 0

# Relationale Constraints
C4: hatWartungsintervall ≤ hatMaxLebensdauer
C5: hatBetriebsstunden ≤ hatMaxLebensdauer

# Domänenspezifische Constraints
C6: Drucksensor.hatMessbereich.max ≤ 1000 bar
C7: Motor.hatDrehzahl zwischen 0 und 10000 rpm
```

### 4.2.4 Laden und Verwalten

In Python mit Owlready2:

```python
from owlready2 import get_ontology, Thing, DataProperty, ObjectProperty

# Ontologie laden
onto = get_ontology("file://maintenance_ontology.owl").load()

# Konzepte abfragen
print(list(onto.classes()))
# [maintenance_ontology.Komponente, maintenance_ontology.Motor, ...]

# Instanz erstellen (für Tests)
with onto:
    motor1 = onto.Motor("Motor_M1")
    motor1.hatBetriebsstunden = [15000]
    motor1.hatMaxLebensdauer = [50000]

# Reasoner ausführen
from owlready2 import sync_reasoner
sync_reasoner(onto)
```

---

## 4.3 Reasoning-Modul

### 4.3.1 Aufgabe

Das Reasoning-Modul ist der **Wächter**. Es prüft, ob die vom Parser extrahierten Daten mit allen Regeln der Ontologie konsistent sind.

**Eingabe:** Strukturierte Daten vom Parser
**Ausgabe:** Konsistenzstatus + Liste der Verletzungen

### 4.3.2 Konsistenzprüfung

Formal prüfen wir, ob die Wissensbasis widerspruchsfrei ist:

```
Gegeben:
- TBox T (Axiome/Regeln)
- ABox A (Instanzdaten)

Prüfe:
- T ∪ A ⊭ ⊥  (Die Kombination impliziert keinen Widerspruch)
```

Wenn ein Widerspruch gefunden wird, sind die Daten inkonsistent.

### 4.3.3 Zwei Reasoning-Strategien

**1. Vollständiges OWL-Reasoning (Tableau-Algorithmus)**

Ein OWL-Reasoner wie HermiT prüft alle Axiome der Ontologie. Das ist vollständig, aber kann bei großen Ontologien langsam sein.

```python
from owlready2 import sync_reasoner_hermit

# Reasoner ausführen
try:
    sync_reasoner_hermit(onto)
    print("Ontologie ist konsistent")
except OwlReadyInconsistentOntologyError:
    print("Inkonsistenz gefunden!")
```

**2. Regelbasiertes Reasoning (schnell, fokussiert)**

Für häufige Constraint-Typen implementieren wir direkte Prüfungen in Python. Das ist schneller, prüft aber nur vordefinierte Regeln.

```python
def check_numeric_constraint(value, min_val=None, max_val=None):
    """Prüft numerische Wertebereiche."""
    violations = []

    if min_val is not None and value < min_val:
        violations.append(f"Wert {value} unter Minimum {min_val}")

    if max_val is not None and value > max_val:
        violations.append(f"Wert {value} über Maximum {max_val}")

    return violations

def check_relational_constraint(val1, val2, operator):
    """Prüft relationale Constraints."""
    if operator == "≤" and not val1 <= val2:
        return f"{val1} ist nicht ≤ {val2}"
    if operator == "<" and not val1 < val2:
        return f"{val1} ist nicht < {val2}"
    return None
```

### 4.3.4 Inkrementelles Reasoning

Für Echtzeit-Anwendungen ist vollständiges Reasoning bei jeder Anfrage zu langsam. Lösung: **Inkrementelles Reasoning** – prüfe nur die von der neuen Assertion betroffenen Axiome.

**Idee:**
```
Neue Assertion: Motor_M1.hatBetriebsstunden = 15000

Betroffene Axiome:
- C1: hatBetriebsstunden ≥ 0  ✓ (15000 ≥ 0)
- C5: hatBetriebsstunden ≤ hatMaxLebensdauer  → prüfen

Nicht betroffene Axiome (überspringen):
- C6: Drucksensor.hatMessbereich.max ≤ 1000
- C7: Motor.hatDrehzahl zwischen 0 und 10000
```

### 4.3.5 Pseudocode: Konsistenzprüfung

```python
def check_consistency(data: StructuredData, ontology: Ontology) -> ConsistencyResult:
    """
    Prüft strukturierte Daten gegen die Ontologie.

    Args:
        data: Die zu prüfenden Daten
        ontology: Die Ontologie mit Regeln

    Returns:
        ConsistencyResult mit Status und Verletzungen
    """
    violations = []

    # 1. Typ-Constraints prüfen
    for entity in data.entities:
        if not ontology.is_valid_type(entity.type):
            violations.append(Violation(
                type="TYPE_ERROR",
                message=f"Unbekannter Typ: {entity.type}"
            ))

    # 2. Wertebereichs-Constraints prüfen
    for entity in data.entities:
        for prop, value in entity.properties.items():
            constraint = ontology.get_range_constraint(entity.type, prop)
            if constraint:
                if value < constraint.min or value > constraint.max:
                    violations.append(Violation(
                        type="RANGE_ERROR",
                        message=f"{prop}={value} außerhalb [{constraint.min}, {constraint.max}]"
                    ))

    # 3. Relationale Constraints prüfen
    for constraint in ontology.relational_constraints:
        if constraint.applies_to(data):
            result = constraint.evaluate(data)
            if not result.satisfied:
                violations.append(Violation(
                    type="RELATIONAL_ERROR",
                    message=result.message
                ))

    # 4. Ergebnis zusammenstellen
    return ConsistencyResult(
        is_consistent=(len(violations) == 0),
        violations=violations
    )
```

### 4.3.6 Ausgabeformat

Das Reasoning-Modul gibt strukturierte Ergebnisse zurück:

```json
{
  "is_consistent": false,
  "violations": [
    {
      "type": "RELATIONAL_ERROR",
      "constraint": "wartungsintervall ≤ max_lebensdauer",
      "message": "Wartungsintervall (60000) übersteigt maximale Lebensdauer (50000)",
      "entity": "Motor_M1",
      "properties": {
        "wartungsintervall": 60000,
        "max_lebensdauer": 50000
      }
    }
  ],
  "checked_constraints": 12,
  "processing_time_ms": 45
}
```

---

## 4.4 Self-Correction Loop

### 4.4.1 Aufgabe

Der Self-Correction Loop ist der **Korrekturmechanismus**. Wenn das Reasoning-Modul Fehler findet, werden diese nicht einfach verworfen, sondern gezielt an das LLM zurückgemeldet mit der Aufforderung zur Korrektur.

### 4.4.2 Der Ablauf

```
┌─────────────────────────────────────────────────────────────────┐
│                   SELF-CORRECTION LOOP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Iteration 0:                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Original │───▶│  Parser  │───▶│ Reasoner │──── ✗ Fehler     │
│  │   Text   │    │          │    │          │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                        │                        │
│                                        ▼                        │
│  Iteration 1:                   ┌──────────────┐               │
│  ┌──────────┐    ┌──────────┐  │  Correction  │               │
│  │ Korrig.  │◀───│   LLM    │◀─│    Prompt    │               │
│  │   Text   │    │          │  │              │               │
│  └────┬─────┘    └──────────┘  └──────────────┘               │
│       │                                                        │
│       ▼                                                        │
│  ┌──────────┐    ┌──────────┐                                  │
│  │  Parser  │───▶│ Reasoner │──── ✓ OK → Ausgabe              │
│  │          │    │          │                                  │
│  └──────────┘    └──────────┘     oder                        │
│                                   ✗ Fehler → Iteration 2...   │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4.3 Generierung des Korrektur-Prompts

Der Korrektur-Prompt muss dem LLM präzise mitteilen, was falsch ist und was erwartet wird:

```
Korrektur-Prompt-Vorlage:
═══════════════════════════════════════════════════════════════════
Der folgende Text enthält logische Fehler oder Inkonsistenzen:

ORIGINAL:
{original_text}

ERKANNTE PROBLEME:
{violations_list}

ANFORDERUNGEN:
- Korrigiere den Text, sodass alle genannten Probleme behoben sind
- Behalte alle korrekten Informationen unverändert bei
- Ändere nur die fehlerhaften Werte/Aussagen
- Antworte mit dem vollständigen korrigierten Text

KORRIGIERTER TEXT:
═══════════════════════════════════════════════════════════════════
```

**Beispiel:**

```
ORIGINAL:
"Motor M1 hat 15.000 Betriebsstunden bei einer maximalen Lebensdauer 
von 10.000 Stunden. Das nächste Wartungsintervall liegt bei 20.000 Stunden."

ERKANNTE PROBLEME:
- Betriebsstunden (15.000) übersteigen maximale Lebensdauer (10.000)
- Wartungsintervall (20.000) übersteigt maximale Lebensdauer (10.000)

ANFORDERUNGEN:
- Korrigiere die Werte so, dass sie konsistent sind
- ...

KORRIGIERTER TEXT:
```

### 4.4.4 Das Konvergenzproblem

**Kritisches Risiko:** Der Self-Correction Loop kann in einen nicht-konvergierenden Zustand geraten, bei dem das LLM zwischen fehlerhaften Antworten oszilliert.

**Beispiel für Oszillation:**
```
Iteration 1: Wartungsintervall = 60000, Lebensdauer = 50000
  → Fehler: Intervall > Lebensdauer
  → Korrektur angefordert

Iteration 2: Wartungsintervall = 40000, Lebensdauer = 30000
  → Fehler: Intervall > Lebensdauer (immer noch!)
  → Korrektur angefordert

Iteration 3: Wartungsintervall = 50000, Lebensdauer = 50000
  → OK? Nein, weiterer Fehler: Betriebsstunden > Lebensdauer
  → Korrektur angefordert

... Loop läuft endlos
```

### 4.4.5 Konvergenzbedingungen

Der Loop konvergiert unter folgenden Bedingungen:

1. **Ontologie ist widerspruchsfrei:** Es gibt einen gültigen Zustand, den das LLM erreichen kann.

2. **LLM produziert monotone Verbesserungen:** Die Anzahl der Fehler sinkt mit jeder Iteration.

3. **Korrektur-Prompts sind präzise:** Das LLM versteht genau, was korrigiert werden muss.

### 4.4.6 Absicherungen

**1. Maximum Iterations**
```python
MAX_ITERATIONS = 5
```

**2. Temperatur = 0**
Reduziert die Variabilität der LLM-Antworten.

**3. Cycle Detection**
Erkennt, wenn das LLM denselben Output wie in einer früheren Iteration produziert.

```python
seen_outputs = set()
for i in range(MAX_ITERATIONS):
    output_hash = hash(llm_output)
    if output_hash in seen_outputs:
        # Zyklus erkannt!
        break
    seen_outputs.add(output_hash)
```

**4. Exponential Backoff bei Prompts**
Bei wiederholten Fehlern werden die Korrektur-Prompts spezifischer:

- Iteration 1: "Bitte korrigiere den Fehler"
- Iteration 2: "Der Wert X muss kleiner als Y sein"
- Iteration 3: "Setze X auf einen Wert ≤ Y, z.B. auf Z"

### 4.4.7 Eskalationsstrategie

Wenn der Loop nach MAX_ITERATIONS nicht konvergiert:

1. **Bestes Ergebnis zurückgeben:** Die Iteration mit den wenigsten Fehlern.

2. **Verbleibende Fehler kennzeichnen:** Klare Markierung, welche Constraints nicht erfüllt sind.

3. **Confidence Score:** Angabe der "Güte" des Ergebnisses (z.B. 80% der Constraints erfüllt).

4. **Optional: Menschliche Eskalation:** Weiterleitung an einen Reviewer.

### 4.4.8 Pseudocode: Self-Correction Loop

```python
def self_correction_loop(
    initial_text: str,
    ontology: Ontology,
    max_iterations: int = 5
) -> ValidationResult:
    """
    Führt den Self-Correction Loop aus.

    Args:
        initial_text: Der zu validierende Text
        ontology: Die Ontologie für Validierung
        max_iterations: Maximale Iterationen

    Returns:
        ValidationResult mit finalem Status
    """
    current_text = initial_text
    seen_hashes = set()
    best_result = None
    best_violation_count = float('inf')

    for iteration in range(max_iterations):
        # Parsing
        parsed_data = parse(current_text, ontology.schema, ontology)
        if parsed_data.is_error:
            return ValidationResult(
                success=False,
                error="PARSE_ERROR",
                message=parsed_data.error_message
            )

        # Konsistenzprüfung
        consistency = check_consistency(parsed_data, ontology)

        # Bestes Ergebnis merken
        if len(consistency.violations) < best_violation_count:
            best_violation_count = len(consistency.violations)
            best_result = ValidationResult(
                success=True,
                data=parsed_data,
                violations=consistency.violations
            )

        # Erfolgreich?
        if consistency.is_consistent:
            return ValidationResult(
                success=True,
                data=parsed_data,
                iterations=iteration + 1
            )

        # Zyklus-Erkennung
        text_hash = hash(current_text)
        if text_hash in seen_hashes:
            break  # Zyklus erkannt
        seen_hashes.add(text_hash)

        # Korrektur anfordern
        correction_prompt = generate_correction_prompt(
            current_text,
            consistency.violations,
            iteration
        )
        current_text = call_llm(correction_prompt, temperature=0)

    # Max Iterations erreicht oder Zyklus
    return ValidationResult(
        success=False,
        error="MAX_ITERATIONS_EXCEEDED",
        best_result=best_result,
        violations=best_result.violations if best_result else []
    )
```

---

## 4.5 Orchestrierung: Das Zusammenspiel

### 4.5.1 Der Orchestrator

Der Orchestrator koordiniert alle Komponenten und stellt die externe API bereit:

```python
class LogicGuardLayer:
    """
    Hauptklasse des Logic-Guard-Layer Systems.
    """

    def __init__(self, ontology_path: str, llm_client, max_iterations: int = 5):
        self.ontology = load_ontology(ontology_path)
        self.parser = SemanticParser(llm_client, self.ontology.schema)
        self.reasoner = ReasoningModule(self.ontology)
        self.corrector = SelfCorrectionLoop(llm_client, max_iterations)

    def validate(self, text: str) -> ValidationResult:
        """
        Validiert einen Text gegen die Ontologie.

        Args:
            text: Der zu validierende Text

        Returns:
            ValidationResult mit Status und Daten
        """
        return self.corrector.run(text, self.parser, self.reasoner)
```

### 4.5.2 Nutzung

```python
# Initialisierung
lgl = LogicGuardLayer(
    ontology_path="maintenance_ontology.owl",
    llm_client=AnthropicClient(api_key="..."),
    max_iterations=5
)

# Validierung
result = lgl.validate("""
    Der Motor M1 hat 15.000 Betriebsstunden bei einer maximalen 
    Lebensdauer von 50.000 Stunden. Das Wartungsintervall beträgt 
    5.000 Stunden.
""")

# Ergebnis verarbeiten
if result.success:
    print("Validierung erfolgreich!")
    print(f"Daten: {result.data}")
else:
    print(f"Validierung fehlgeschlagen: {result.error}")
    print(f"Verletzungen: {result.violations}")
```

---

## 4.6 Zusammenfassung Modul 4

### Kernaussagen

1. **Der Parser** transformiert Text in Struktur durch LLM-gestütztes Schema-Guided Parsing.

2. **Die Ontologie** definiert das Weltwissen und die Regeln der Domäne.

3. **Der Reasoner** prüft Konsistenz durch Tableau-Algorithmus oder regelbasierte Checks.

4. **Der Self-Correction Loop** ermöglicht iterative Korrektur mit Absicherungen gegen Nicht-Konvergenz.

5. **Der Orchestrator** koordiniert alle Komponenten und stellt eine einfache API bereit.

---

## Übung 4: Komponenten-Interaktion

**Aufgabe:** Trace den Validierungsprozess für folgenden Input.

**Input-Text:**
```
"Die Hydraulikpumpe HP-01 zeigt einen Betriebsdruck von 420 bar bei 
12.000 Betriebsstunden. Die maximale Lebensdauer beträgt 10.000 Stunden. 
Das nächste Wartungsintervall ist auf 15.000 Stunden eingestellt."
```

**Ontologie-Regeln:**
```
R1: Betriebsstunden ≥ 0
R2: Betriebsstunden ≤ max_lebensdauer
R3: 0 < Betriebsdruck ≤ 350 bar (für Standard-Hydraulik)
R4: Wartungsintervall ≤ max_lebensdauer
```

**Aufgaben:**
1. Führe das Parsing durch (extrahiere strukturierte Daten)
2. Führe die Konsistenzprüfung durch (welche Regeln verletzt?)
3. Formuliere einen Korrektur-Prompt
4. Wie könnte eine korrigierte Version aussehen?

---

# Modul 5: Technische Risiken

**Lernziele:** Nach diesem Modul verstehst du die fundamentalen technischen Risiken des Logic-Guard-Layer-Ansatzes und wie man mit ihnen umgeht.

**Geschätzte Dauer:** 2 Stunden

---

## 5.1 Risiko 1: Semantic Loss

### Das Problem

Bei der Transformation von natürlicher Sprache in formale Logik gehen unweigerlich Informationen verloren. Natürliche Sprache enthält Nuancen, die sich nicht binär abbilden lassen:

**Beispiele für schwierige Fälle:**

1. **Unsicherheitsausdrücke:**
   ```
   "Der Motor hat vermutlich etwa 15.000 Betriebsstunden."

   → Welchen Wert extrahieren? 15.000? "unbekannt"?
   → Die Unsicherheit geht verloren.
   ```

2. **Implizite Aussagen:**
   ```
   "Die Wartung wurde wie üblich durchgeführt."

   → Was bedeutet "wie üblich"?
   → Implizites Wissen fehlt der Ontologie.
   ```

3. **Ironie/Kontext:**
   ```
   "Der Motor läuft 'perfekt' - solange man die Geräusche ignoriert."

   → Ironie wird nicht erkannt.
   → Falsch-positiv: Motor wird als "perfekt" klassifiziert.
   ```

4. **Domänenspezifischer Jargon:**
   ```
   "Die Pumpe hat einen Heuler."

   → Umgangssprachlich für ein bestimmtes Geräusch.
   → Ontologie kennt nur formale Begriffe.
   ```

### Die Balance: Precision vs. Recall

Beim Umgang mit Semantic Loss muss eine Balance gefunden werden:

**Zu strikte Filter (hohe Precision, niedriger Recall):**
- Viele valide Aussagen werden fälschlich abgelehnt
- Benutzerfrustration ("Das System akzeptiert nichts")
- Wichtige Informationen gehen verloren

**Zu lockere Filter (niedriger Precision, hoher Recall):**
- Fehlerhafte Aussagen werden durchgelassen
- Der Zweck des Systems wird verfehlt
- Halluzinationen erreichen die Endanwendung

### Strategien

1. **Konfidenz-Modellierung:**
   - Parser gibt Konfidenzwerte für Extraktionen an
   - Niedrige Konfidenz → manuelle Prüfung

2. **Unsicherheits-Handling:**
   - Eigene Klasse für unsichere Werte
   - Weitergabe der Unsicherheit an Endanwendung

3. **Iterative Ontologie-Verbesserung:**
   - Analyse von Falsch-Positiven und Falsch-Negativen
   - Kontinuierliche Anpassung der Regeln

---

## 5.2 Risiko 2: Feedback-Loop-Stabilität

### Das Problem

Der Self-Correction Loop kann in pathologische Zustände geraten:

**1. Oszillation:**
Das LLM wechselt zwischen zwei oder mehr fehlerhaften Zuständen.

```
Iteration 1: A = 100, B = 50  → Fehler: A > B verletzt
Iteration 2: A = 40, B = 50   → Fehler: A < 45 verletzt (andere Regel)
Iteration 3: A = 100, B = 50  → Zurück zu Iteration 1!
```

**2. Divergenz:**
Die Fehler werden mit jeder Iteration schlimmer.

```
Iteration 1: Betriebsstunden = 15000 (Fehler: > 10000)
Iteration 2: Betriebsstunden = 50000 (LLM "korrigiert" in falsche Richtung)
Iteration 3: Betriebsstunden = 100000 (noch schlimmer)
```

**3. Stuck State:**
Das LLM wiederholt exakt denselben Output.

```
Iteration 1: "Der Wert beträgt X"
Iteration 2: "Der Wert beträgt X" (ignoriert Korrekturhinweis)
Iteration 3: "Der Wert beträgt X"
```

### Theoretische Grundlage

Konvergenz ist nur unter bestimmten Bedingungen garantiert:

**Theorem (Konvergenzbedingungen):**
Der Self-Correction Loop konvergiert, wenn:
1. Die Ontologie widerspruchsfrei ist (es existiert ein gültiger Zustand)
2. Das LLM monotone Verbesserungen produziert (Fehleranzahl sinkt)
3. Die Korrektur-Prompts hinreichend spezifisch sind

**Problem:** Bedingung 2 kann bei realen LLMs nicht garantiert werden.

### Praktische Absicherungen

1. **Hard Limits:**
   ```python
   MAX_ITERATIONS = 5  # Absolutes Maximum
   MAX_SAME_ERROR = 2   # Gleicher Fehler max. 2x
   ```

2. **Cycle Detection:**
   ```python
   if current_hash in previous_hashes:
       return CYCLE_DETECTED
   ```

3. **Prompt-Eskalation:**
   ```python
   if iteration > 2:
       use_more_specific_prompt()
   if iteration > 3:
       provide_explicit_solution_hint()
   ```

4. **Graceful Degradation:**
   - Beste bisherige Lösung zurückgeben
   - Verbleibende Fehler explizit kennzeichnen
   - Confidence Score angeben

---

## 5.3 Risiko 3: Latenz-Anforderungen

### Das Problem

Die Integration symbolischen Reasonings erhöht die Verarbeitungszeit erheblich:

**Typische Latenzen:**
| Komponente | Latenz (p50) | Latenz (p99) |
|------------|--------------|--------------|
| LLM-Aufruf | 200ms | 500ms |
| Parsing | 50ms | 150ms |
| OWL-Reasoning | 100ms | 500ms |
| **Gesamt (1 Iteration)** | **350ms** | **1150ms** |
| **Mit 3 Korrekturen** | **1050ms** | **3450ms** |

Für interaktive Anwendungen (Chat, Echtzeit-Assistenten) sind Latenzen > 1 Sekunde problematisch.

### Strategien

**1. Inkrementelles Reasoning:**
- Prüfe nur betroffene Axiome
- Nutze Caching für häufige Prüfungen

**2. Regelbasierte Schnellprüfung:**
- Implementiere häufige Constraints direkt in Python
- OWL-Reasoning nur für komplexe Fälle

**3. Asynchrone Validierung:**
- Für nicht-kritische Anwendungen: Validierung im Hintergrund
- Sofortige Antwort + spätere Korrektur/Warnung

**4. Gestufte Validierung:**
```
Stufe 1: Schnelle Checks (< 100ms)
  → Typ-Constraints, Wertebereiche

Stufe 2: Vollständige Validierung (< 500ms)
  → Relationale Constraints

Stufe 3: Deep Reasoning (< 2000ms)
  → Komplexe Schlussfolgerungen
```

**5. Parallelisierung:**
- Unabhängige Constraints parallel prüfen
- Multi-Threading für Reasoner-Aufrufe

---

## 5.4 Risiko 4: Ontologie-Vollständigkeit

### Das Problem

Eine Ontologie kann niemals alle Regeln einer Domäne vollständig abbilden. Es gibt immer:

**1. Unbekannte Unbekannte:**
Regeln, an die niemand gedacht hat, bis ein Fehler auftritt.

**2. Implizites Expertenwissen:**
Wissen, das Experten "einfach wissen", aber nicht formalisiert haben.

**3. Randfälle:**
Seltene Situationen, die in der Ontologie nicht modelliert sind.

**4. Evolvierende Domänen:**
Die Realität ändert sich, die Ontologie bleibt zurück.

### Beispiel

```
Ontologie-Regel: Betriebsstunden ≤ max_Lebensdauer

Realität: Bei Komponente X kann die Lebensdauer durch Überholung 
         verlängert werden. Nach Überholung sind die Betriebsstunden 
         wieder höher als die ursprüngliche max_Lebensdauer.

→ Die Ontologie kennt das Konzept "Überholung" nicht.
→ Valide Fälle werden als Fehler markiert.
```

### Strategien

**1. Expliziter Scope:**
- Klar definieren, was geprüft wird
- Dokumentieren, was NICHT geprüft wird
- Benutzer über Limitationen informieren

**2. Iterative Verbesserung:**
- Systematische Analyse von Falsch-Positiven
- Regelmäßige Reviews mit Domänenexperten
- Versionierung der Ontologie

**3. Feedback-Mechanismus:**
- Benutzer können "falsche" Ablehnungen melden
- Automatische Erfassung von Edge Cases
- Priorisierte Ontologie-Erweiterung

**4. Fallback-Strategien:**
- Bei "unknown" Konzepten: Warnung statt Ablehnung
- Manuelle Review-Queue für unklare Fälle

---

## 5.5 Zusammenfassung Modul 5

### Die vier Kernrisiken

| Risiko | Kern-Problem | Hauptstrategie |
|--------|--------------|----------------|
| Semantic Loss | Sprachliche Nuancen gehen verloren | Balance Precision/Recall |
| Feedback-Stabilität | Loop konvergiert nicht | Hard Limits + Cycle Detection |
| Latenz | Reasoning ist langsam | Inkrementell + Caching |
| Vollständigkeit | Ontologie deckt nicht alles ab | Expliziter Scope + Iteration |

### Die zentrale Einsicht

> **Es gibt keine perfekte Lösung.** Jede Strategie ist ein Trade-off. Die Kunst liegt darin, die richtigen Trade-offs für den konkreten Anwendungsfall zu wählen.

---

## Übung 5: Risiko-Analyse

**Aufgabe:** Analysiere folgendes Szenario auf die vier Kernrisiken.

**Szenario:** Logic-Guard-Layer soll für die Validierung von medizinischen Diagnose-Berichten eingesetzt werden.

**Fragen:**

1. **Semantic Loss:** Welche medizinischen Formulierungen könnten problematisch sein?

2. **Feedback-Stabilität:** Warum könnte der Correction Loop in der Medizin besonders riskant sein?

3. **Latenz:** In welchen medizinischen Szenarien ist Latenz kritisch?

4. **Vollständigkeit:** Warum ist medizinisches Wissen besonders schwer vollständig abzubilden?

---

# Modul 6: Architekturentscheidungen

**Lernziele:** Nach diesem Modul verstehst du die praktischen Implementierungsentscheidungen: Speicheroptionen, Technologie-Stack und Code-Organisation.

**Geschätzte Dauer:** 2 Stunden

---

## 6.1 Speicheroptionen für die Ontologie

### 6.1.1 Option 1: In-Memory (Prototyp)

Die Ontologie wird als OWL-Datei im Projekt abgelegt und beim App-Start in den Speicher geladen.

```
Projekt/
├── ontology/
│   └── maintenance.owl    ← Ontologie-Datei
├── src/
│   └── ...
└── ...
```

**Vorteile:**
- Einfachste Lösung
- Schnellste Zugriffszeiten
- Keine externe Infrastruktur
- Versionierbar mit Git

**Nachteile:**
- Änderungen erfordern Neustart
- Speicherverbrauch pro Instanz
- Nicht für Multi-Instanz geeignet

**Empfohlen für:** Prototyp, Entwicklung, kleine Deployments

### 6.1.2 Option 2: SQLite/JSON (Einfache Persistenz)

Die Ontologie wird in einer lokalen Datei gespeichert (SQLite-DB oder JSON).

```python
# Schema in SQLite
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY,
    name TEXT,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES concepts(id)
);

CREATE TABLE constraints (
    id INTEGER PRIMARY KEY,
    type TEXT,
    expression TEXT,
    error_message TEXT
);
```

**Vorteile:**
- Einfache Persistenz
- Änderungen ohne Neustart möglich
- Strukturierte Abfragen möglich

**Nachteile:**
- Mapping OWL ↔ relational erforderlich
- Kein eingebautes Reasoning

**Empfohlen für:** Projekte mit dynamischen Ontologie-Updates

### 6.1.3 Option 3: PostgreSQL (Produktion)

Ontologie und Instanzdaten in einer zentralen Datenbank.

**Variante A: Hybrid**
- Schema (TBox) als OWL-Datei
- Instanzen (ABox) in PostgreSQL

**Variante B: Vollständig relational**
- Alles in PostgreSQL
- Custom Mapping-Schicht

**Vorteile:**
- Skalierbar
- Multi-User/Multi-Instanz
- ACID-Transaktionen

**Nachteile:**
- Infrastruktur-Overhead
- Komplexeres Setup

**Empfohlen für:** Produktionsumgebungen, Enterprise

### 6.1.4 Option 4: Triple Store (Knowledge Graph)

Spezialisierte Graph-Datenbank für RDF/OWL.

**Beispiele:** Apache Jena, GraphDB, Amazon Neptune

**Vorteile:**
- Natives RDF/OWL-Format
- SPARQL-Abfragen
- Eingebautes Reasoning
- Skaliert für Millionen von Tripeln

**Nachteile:**
- Zusätzliche Technologie
- Lernkurve für SPARQL

**Empfohlen für:** Große Knowledge Graphs, komplexe Abfragen

### 6.1.5 Empfehlung: Stufenweise Migration

```
Stufe 1 (Prototyp):     OWL-Datei + In-Memory
         ↓
Stufe 2 (MVP):          OWL-Datei + Redis-Cache
         ↓
Stufe 3 (Produktion):   PostgreSQL + Cache
         ↓
Stufe 4 (Enterprise):   Triple Store
```

---

## 6.2 Technologie-Stack

### 6.2.1 Empfohlener Stack

| Komponente | Technologie | Begründung |
|------------|-------------|------------|
| Sprache | Python 3.11+ | LLM-Ecosystem, Bibliotheken |
| Web-Framework | FastAPI | Async, Modern, Type Hints |
| Ontologie-Sprache | OWL 2 / RDF | W3C-Standard |
| OWL-Bibliothek | Owlready2 | Python-nativ, einfache API |
| Reasoner | HermiT | Schnell, vollständig |
| LLM-Client | Anthropic/OpenAI SDK | Offizielle Bibliotheken |
| Datenformat | JSON-LD | RDF-kompatibel, lesbar |
| Caching | Redis (optional) | Schnell, verteilt |

### 6.2.2 Python-Abhängigkeiten

```
# requirements.txt
fastapi>=0.100.0
uvicorn>=0.23.0
owlready2>=0.40
anthropic>=0.18.0       # oder openai>=1.0.0
pydantic>=2.0.0
redis>=4.0.0            # optional
python-multipart>=0.0.6
```

### 6.2.3 Owlready2 Kurzübersicht

```python
from owlready2 import get_ontology, Thing, DataProperty, ObjectProperty

# Ontologie laden
onto = get_ontology("file://maintenance.owl").load()

# Klassen definieren (wenn nicht aus Datei)
with onto:
    class Komponente(Thing):
        pass

    class Motor(Komponente):
        pass

    class hatBetriebsstunden(DataProperty):
        domain = [Komponente]
        range = [int]

# Instanz erstellen
with onto:
    m1 = Motor("Motor_M1")
    m1.hatBetriebsstunden = [15000]

# Reasoner
from owlready2 import sync_reasoner_hermit
sync_reasoner_hermit(onto)

# Abfragen
print(list(onto.Motor.instances()))
```

---

## 6.3 Code-Organisation

### 6.3.1 Modul-Struktur

```
logic_guard_layer/
├── __init__.py
├── main.py                    # FastAPI-App
├── config.py                  # Konfiguration
│
├── core/                      # Kernlogik
│   ├── __init__.py
│   ├── orchestrator.py        # Hauptsteuerung
│   ├── parser.py              # Semantischer Parser
│   ├── reasoner.py            # Reasoning-Modul
│   └── corrector.py           # Self-Correction Loop
│
├── ontology/                  # Ontologie-Handling
│   ├── __init__.py
│   ├── loader.py              # Laden der Ontologie
│   ├── validator.py           # Schema-Validierung
│   └── constraints.py         # Constraint-Definitionen
│
├── llm/                       # LLM-Integration
│   ├── __init__.py
│   ├── client.py              # API-Abstraktion
│   └── prompts.py             # Prompt-Templates
│
├── models/                    # Datenmodelle
│   ├── __init__.py
│   ├── entities.py            # Domain-Entities
│   └── responses.py           # API-Responses
│
├── utils/                     # Hilfsfunktionen
│   ├── __init__.py
│   ├── logging.py
│   └── metrics.py
│
├── data/                      # Ontologie-Dateien
│   └── maintenance.owl
│
└── tests/                     # Tests
    ├── __init__.py
    ├── test_parser.py
    ├── test_reasoner.py
    └── test_integration.py
```

### 6.3.2 Verantwortlichkeiten

**core/orchestrator.py:**
- Koordiniert den Validierungsfluss
- Stellt die öffentliche API bereit

**core/parser.py:**
- Text → Strukturierte Daten
- Prompt-Generierung für Parsing
- JSON-Validierung

**core/reasoner.py:**
- Konsistenzprüfung gegen Ontologie
- Regelbasierte und OWL-Reasoning
- Fehlersammlung

**core/corrector.py:**
- Self-Correction Loop
- Korrektur-Prompt-Generierung
- Konvergenz-Kontrolle

**ontology/loader.py:**
- Laden der OWL-Datei
- Initialisierung des Reasoners
- Caching

**llm/client.py:**
- Abstraktion über verschiedene LLM-APIs
- Retry-Logik
- Rate Limiting

### 6.3.3 FastAPI-Endpunkte

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Logic-Guard-Layer")

class ValidationRequest(BaseModel):
    text: str
    schema_name: str = "default"

class ValidationResponse(BaseModel):
    success: bool
    data: dict | None = None
    violations: list[dict] = []
    iterations: int = 0

@app.post("/validate", response_model=ValidationResponse)
async def validate(request: ValidationRequest):
    """Validiert einen Text gegen die Ontologie."""
    result = await logic_guard.validate(
        text=request.text,
        schema=request.schema_name
    )
    return ValidationResponse(
        success=result.success,
        data=result.data,
        violations=result.violations,
        iterations=result.iterations
    )

@app.get("/health")
async def health():
    """Health-Check für Load Balancer."""
    return {"status": "healthy"}
```

---

## 6.4 Performance-Optimierungen

### 6.4.1 Caching-Strategie

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHING-ARCHITEKTUR                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Ontologie-Cache (In-Memory)                          │
│  - TBox beim Start laden                                       │
│  - Klassen, Properties, Axiome                                 │
│                                                                 │
│  Layer 2: Reasoning-Cache (In-Memory/Redis)                    │
│  - Häufige Constraint-Prüfungen                                │
│  - TTL: 1 Stunde                                               │
│                                                                 │
│  Layer 3: LLM-Cache (Redis)                                    │
│  - Identische Prompts                                          │
│  - TTL: 24 Stunden                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4.2 Parallelisierung

```python
import asyncio

async def check_constraints_parallel(data, constraints):
    """Prüft unabhängige Constraints parallel."""
    tasks = [
        check_constraint(data, c) 
        for c in constraints 
        if c.is_independent
    ]
    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

### 6.4.3 Lazy Loading

```python
class OntologyLoader:
    _instance = None
    _ontology = None

    @classmethod
    def get_ontology(cls):
        """Lädt Ontologie lazy beim ersten Zugriff."""
        if cls._ontology is None:
            cls._ontology = load_ontology_from_file()
        return cls._ontology
```

---

## 6.5 Zusammenfassung Modul 6

### Kernentscheidungen

| Frage | Prototyp | Produktion |
|-------|----------|------------|
| Ontologie-Speicher | OWL-Datei + In-Memory | PostgreSQL + Cache |
| Framework | FastAPI | FastAPI |
| OWL-Bibliothek | Owlready2 | Owlready2 |
| Reasoning | HermiT | HermiT + Regelbasiert |
| Caching | In-Memory | Redis |

### Die Architektur-Philosophie

> **Starte einfach, skaliere bei Bedarf.** Eine OWL-Datei und Owlready2 reichen für den Prototyp. Die Architektur erlaubt spätere Erweiterung, ohne das Validierungskonzept zu ändern.

---

# Modul 7: Synthese und Ausblick

**Lernziele:** Nach diesem Modul kannst du das Gesamtsystem zusammenfassen, die Übertragbarkeit auf andere Domänen einschätzen und offene Forschungsfragen benennen.

**Geschätzte Dauer:** 2 Stunden

---

## 7.1 Zusammenfassung: Das Gesamtbild

### Die Kernidee in drei Sätzen

1. **LLMs sind mächtig, aber unzuverlässig.** Sie generieren sprachlich kohärente, aber potenziell faktisch falsche Outputs.

2. **Symbolische Logik ist zuverlässig, aber unflexibel.** Sie kann harte Garantien geben, aber nicht mit natürlicher Sprache umgehen.

3. **Logic-Guard-Layer kombiniert beide.** Das LLM generiert, die Ontologie validiert – nur geprüfte Outputs erreichen die Endanwendung.

### Die Architektur auf einen Blick

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LOGIC-GUARD-LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────┐                                                       │
│   │  LLM    │────┐                                                  │
│   └─────────┘    │                                                  │
│                  ▼                                                  │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    VALIDIERUNGS-PIPELINE                     │  │
│   │                                                              │  │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────────────┐      │  │
│   │   │  Parser  │───▶│ Reasoner │───▶│ Self-Correction  │      │  │
│   │   └──────────┘    └────┬─────┘    └────────┬─────────┘      │  │
│   │                        │                   │                 │  │
│   │                        ▼                   │                 │  │
│   │                 ┌──────────┐               │                 │  │
│   │                 │ Ontologie│               │                 │  │
│   │                 └──────────┘               │                 │  │
│   │                                            │                 │  │
│   └────────────────────────────────────────────┼─────────────────┘  │
│                                                │                    │
│                                                ▼                    │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │               VALIDIERTE DATEN                               │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Was das System leistet

**Garantien:**
- Alle definierten Constraints werden geprüft
- Nur konsistente Outputs werden weitergegeben
- Verletzungen werden explizit dokumentiert

**Keine Garantien:**
- Vollständigkeit (nur modellierte Regeln werden geprüft)
- 100% Konvergenz des Correction Loops
- Erhaltung aller sprachlichen Nuancen

---

## 7.2 Domänentransfer

### Das Prinzip

Die Logic-Guard-Layer-Architektur ist **domänenunabhängig** konzipiert. Die Kernkomponenten (Parser, Reasoner, Corrector) bleiben unverändert. Nur die Ontologie wird ausgetauscht.

```
Domäne A (Wartung):     Architektur  +  Ontologie_A
Domäne B (Medizin):     Architektur  +  Ontologie_B
Domäne C (Recht):       Architektur  +  Ontologie_C
```

### Schritte für eine neue Domäne

1. **Domänenanalyse:**
   - Welche Konzepte sind relevant?
   - Welche Regeln gelten?
   - Welche Fehlerarten sollen erkannt werden?

2. **Ontologie-Erstellung:**
   - Konzepte und Hierarchien definieren
   - Properties festlegen
   - Constraints formalisieren

3. **Schema-Definition:**
   - Welche Struktur soll der Parser extrahieren?
   - Welche Felder sind Pflicht?

4. **Prompt-Anpassung:**
   - Parsing-Prompts an Domäne anpassen
   - Korrektur-Prompts mit Domänenwissen anreichern

5. **Test und Iteration:**
   - Mit Testdaten validieren
   - Ontologie bei Bedarf erweitern

### Beispiele für Domänen

**Technische Wartung:**
- Komponenten, Anlagen, Messwerte
- Wartungsintervalle, Lebensdauern
- Physikalische Plausibilität

**Qualitätssicherung:**
- Prüfberichte, Messprotokolle
- Normen und Spezifikationen
- Grenzwerte und Toleranzen

**Compliance:**
- Regulatorische Anforderungen
- Dokumentationspflichten
- Fristen und Nachweise

**Medizin:**
- Diagnosen, Medikamente, Dosierungen
- Wechselwirkungen, Kontraindikationen
- Leitlinien und Protokolle

**Recht:**
- Verträge, Klauseln, Bedingungen
- Gesetzesverweise, Fristen
- Logische Konsistenz von Vereinbarungen

---

## 7.3 Offene Forschungsfragen

### 7.3.1 Automatische Ontologie-Generierung

**Problem:** Die manuelle Erstellung von Ontologien ist aufwändig und fehleranfällig.

**Forschungsfrage:** Können LLMs selbst Ontologien aus Fachtexten extrahieren?

**Ansätze:**
- LLM-gestützte Konzeptextraktion aus Dokumenten
- Semi-automatische Ontologie-Verfeinerung
- Crowdsourcing mit Expertenvalidierung

**Herausforderungen:**
- Qualitätssicherung der extrahierten Ontologie
- Konsistenz über verschiedene Quellen
- Integration von implizitem Expertenwissen

### 7.3.2 Probabilistisches Reasoning

**Problem:** Aktuelle Ontologien arbeiten binär (wahr/falsch). Reale Welt hat Unsicherheiten.

**Forschungsfrage:** Wie kann Unsicherheit in das Reasoning integriert werden?

**Ansätze:**
- Probabilistische Beschreibungslogik
- Fuzzy-Logik für graduelle Wahrheitswerte
- Bayessche Netze für Wahrscheinlichkeitsmodellierung

**Herausforderungen:**
- Skalierbarkeit probabilistischer Reasoner
- Integration mit bestehenden OWL-Tools
- Interpretation von Konfidenzwerten

### 7.3.3 Aktives Lernen

**Problem:** Ontologien veralten und haben Lücken.

**Forschungsfrage:** Wie kann das System aus Feedback lernen?

**Ansätze:**
- Benutzer-Feedback zu Falsch-Positiven/-Negativen
- Automatische Erkennung von Ontologie-Lücken
- Vorschläge für Ontologie-Erweiterungen

**Herausforderungen:**
- Vermeidung von Bias durch Benutzer-Feedback
- Automatische Qualitätsprüfung von Vorschlägen
- Versionierung und Rollback

### 7.3.4 Multi-Modale Erweiterung

**Problem:** Technische Dokumentation enthält oft Bilder, Diagramme, Tabellen.

**Forschungsfrage:** Wie können nicht-textuelle Inhalte validiert werden?

**Ansätze:**
- Vision-Language-Modelle für Bildanalyse
- Tabellen-Parsing und -Validierung
- Diagramm-Interpretation (P&ID, Schaltpläne)

**Herausforderungen:**
- Integration verschiedener Modalitäten
- Konsistenz zwischen Text und Bild
- Erweiterte Ontologien für visuelle Konzepte

---

## 7.4 Praktische nächste Schritte

### Für den Einstieg

1. **Owlready2 installieren und Tutorial durcharbeiten**
   - Dokumentation: https://owlready2.readthedocs.io/

2. **Kleine Test-Ontologie erstellen**
   - 5-10 Konzepte, 3-5 Constraints
   - Mit Testdaten validieren

3. **Parser-Prompt entwickeln**
   - Für die Test-Ontologie
   - Mit echtem LLM testen

4. **Minimalen Prototyp bauen**
   - Parser + Reasoner + einfacher Loop
   - Ohne Optimierungen

### Für die Vertiefung

1. **Komplexere Ontologie entwickeln**
   - Reale Domäne modellieren
   - Mit Domänenexperten validieren

2. **Performance-Optimierungen implementieren**
   - Caching, Inkrementelles Reasoning
   - Latenz messen und optimieren

3. **Produktions-Setup aufbauen**
   - FastAPI-Service
   - Docker-Deployment
   - Monitoring

---

## 7.5 Fazit

### Die zentrale Botschaft

> **Logic-Guard-Layer ermöglicht den Einsatz von LLMs in Anwendungen, wo Fehler inakzeptabel sind.**

Die Kombination aus neuronaler Flexibilität und symbolischer Zuverlässigkeit öffnet Anwendungsfelder, die bisher für LLMs verschlossen waren: Technische Dokumentation, regulierte Industrien, sicherheitskritische Systeme.

### Die Einschränkungen

Das System ist keine Wunderwaffe:
- Es ist nur so gut wie die Ontologie
- Es kann nicht alle Fehlerarten erkennen
- Es erhöht die Komplexität und Latenz

### Der Ausblick

Die neuro-symbolische KI ist ein aktives Forschungsfeld. Die hier vorgestellte Architektur ist ein pragmatischer Ansatz für den heutigen Stand der Technik. Mit fortschreitender Forschung werden sich neue Möglichkeiten ergeben – automatische Ontologie-Generierung, probabilistisches Reasoning, multimodale Validierung.

Die Grundprinzipien bleiben jedoch bestehen:
- **Validierung statt blindes Vertrauen**
- **Explizite Regeln statt impliziter Hoffnung**
- **Hybride Architekturen statt Entweder-Oder**

---

## Abschluss-Übung: Eigenes Projekt konzipieren

**Aufgabe:** Entwirf ein Konzept für den Einsatz von Logic-Guard-Layer in einer Domäne deiner Wahl.

**Liefergegenstände:**

1. **Domänenbeschreibung:** Was ist die Anwendung? Warum ist Validierung wichtig?

2. **Konzept-Liste:** Mindestens 10 relevante Konzepte mit Hierarchie.

3. **Constraint-Liste:** Mindestens 5 Constraints, die geprüft werden sollen.

4. **Beispiel-Trace:** Ein Beispiel-Input, der validiert werden soll (mit erwartetem Ergebnis).

5. **Risiko-Analyse:** Welche der vier Kernrisiken sind in dieser Domäne besonders relevant?

---

# Anhang A: Glossar

| Begriff | Definition |
|---------|------------|
| **ABox** | Assertional Box – Instanzdaten in einer Wissensbasis |
| **Axiom** | Logische Regel in einer Ontologie |
| **Constraint** | Bedingung, die erfüllt sein muss |
| **Halluzination** | Faktisch inkorrekte LLM-Ausgabe |
| **Knowledge Graph** | Ontologie mit befüllten Instanzdaten |
| **LLM** | Large Language Model |
| **Ontologie** | Formale Spezifikation einer Konzeptualisierung |
| **OWL** | Web Ontology Language |
| **Parsing** | Transformation von Text in strukturierte Daten |
| **RAG** | Retrieval-Augmented Generation |
| **Reasoning** | Ableitung neuer Fakten aus vorhandenen |
| **Semantic Loss** | Informationsverlust bei Formalisierung |
| **TBox** | Terminological Box – Schema/Regeln einer Wissensbasis |

---

# Anhang B: Weiterführende Ressourcen

## Literatur

1. **Garcez, A. d'Avila et al. (2020):** "Neurosymbolic AI: The 3rd Wave" – arXiv:2012.05876

2. **Marcus, G. (2020):** "The Next Decade in AI: Four Steps Towards Robust Artificial Intelligence" – arXiv:2002.06177

3. **Hitzler, P. & Sarker, M.K. (2022):** "Neuro-Symbolic Artificial Intelligence: The State of the Art" – IOS Press

## Online-Ressourcen

- **Owlready2 Dokumentation:** https://owlready2.readthedocs.io/
- **Protégé (Ontologie-Editor):** https://protege.stanford.edu/
- **W3C OWL Spezifikation:** https://www.w3.org/TR/owl2-overview/

## Tools

- **HermiT Reasoner:** http://www.hermit-reasoner.com/
- **Pellet Reasoner:** https://github.com/stardog-union/pellet
- **GraphDB:** https://graphdb.ontotext.com/

---

*Ende der Schulungsunterlagen*

**Version:** 1.0  
**Stand:** Dezember 2024  
**Gesamtumfang:** ca. 20 Stunden Lernzeit