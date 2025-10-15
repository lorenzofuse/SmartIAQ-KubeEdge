[Tesi_Fusè_Lorenzo_753168.pdf](https://github.com/user-attachments/files/22922341/Tesi_Fuse_Lorenzo_753168.pdf)# SmartIAQ – KubeEdge

Progetto di tesi triennale: **Configurazione ed implementazione di una rete basata su microservizi tramite la piattaforma KubeEdge**  
Autore: *Lorenzo Fusè*  
Università degli Studi dell’Insubria – A.A. 2024/2025

---

## 🎯 Obiettivo

Il progetto realizza un’infrastruttura **edge–cloud** basata su **microservizi containerizzati**, con orchestrazione tramite **KubeEdge**.  
Lo scenario d’uso riguarda il monitoraggio della qualità dell’aria indoor (*Indoor Air Quality – IAQ*) e delle risorse virtuali di un ambiente distribuito.

---

## ⚙️ Architettura generale

L’architettura si articola su due livelli principali:

- **Nodo CloudCore**  
  Coordina la rete, riceve e valida i dati pubblicati dai nodi edge, gestisce la persistenza tramite **PostgreSQL** e la visualizzazione tramite **Grafana**.  
  Componenti principali:
  - `subscriber/` – ricezione e decifratura dei messaggi IAQ  
  - `metrics-subscriber/` – raccolta e persistenza delle metriche di sistema  
  - `manifests/` – file YAML per il deploy su MicroK8s / KubeEdge  

- **Nodi Edge (EdgeCore)**  
  Simulano sensori e pubblicano dati cifrati e firmati digitalmente tramite protocollo **MQTT (Mosquitto)**.  
  Componenti principali:
  - `iaq-publisher-zoneX/` – pubblicazione dei parametri ambientali  
  - `vm-metrics-publisher/` – invio delle metriche delle VM  
  - `manifests/` – configurazioni di deploy lato edge  

La comunicazione è cifrata mediante **ECDHE + AES-256 in modalità CFB**, con firma **ECDSA** per garantire integrità e autenticità.

---

## 🧱 Struttura della repository

| Cartella | Contenuto |
|-----------|-----------|
| **CloudCore/** | Microservizi lato cloud e file di deploy |
| **EdgeCore/** | Microservizi lato edge e publisher |
| **SmartIAQ/** | Materiale di supporto: diagrammi, demo, dashboard e riassunto tesi |
| **dataset/** | Dataset di riferimento (*BuildPred – Grenoble*) utilizzato per i test |

---


## 📎 Riferimento completo

Il dettaglio dell’implementazione, delle configurazioni e delle metriche di valutazione è riportato nel **capitolo di implementazione** della tesi di laurea allegata.

📄 *[Tesi completa – “Configurazione ed implementazione di una rete basata su microservizi tramite la piattaforma KubeEdge”]*(https://github.com/user-attachments/files/22922343/Tesi_Fuse_Lorenzo_753168.pdf)

Autore: *Lorenzo Fusè*, Relatrice: *Prof.ssa Alessandra Rizzardi*, Correlatrice: *Prof.ssa Sabrina Sicari* 
Università degli Studi dell’Insubria, A.A. 2024/2025
