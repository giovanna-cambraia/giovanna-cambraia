<div align="center">

<!-- Sharp Metallic Header -->
<img src="https://capsule-render.vercel.app/api?type=rect&color=0:09090b,50:1f2124,100:09090b&height=130&section=header&text=GIOVANNA%20CAMBRAIA&fontColor=d0d3d6&fontSize=38&fontAlignY=42&desc=AVIONICS%20%E2%96%AA%20FLIGHT%20SOFTWARE%20%E2%96%AA%20HIGH-INTEGRITY%20SYSTEMS&descColor=7d828a&descSize=13&descAlignY=68" width="100%"/>

<!-- Monospace Telemetry Status Bar -->
<code>SYS.ID: GC-BR // TARGET: DO-178C [DAL-A/B] · DO-333 · ARP4754B // STATUS: NOMINAL</code>

<br><br>

![Focus](https://img.shields.io/badge/FOCUS-FLIGHT_CONTROL_%26_EMBEDDED-09090b?style=flat-square&labelColor=1f2124&color=09090b)
![Core](https://img.shields.io/badge/CORE-SPARK_ADA_2014_%7C_C11-09090b?style=flat-square&labelColor=1f2124&color=09090b)
![Academic](https://img.shields.io/badge/TARGET-USP_%C2%B7_ITA_%C2%B7_INPE-09090b?style=flat-square&labelColor=1f2124&color=09090b)

</div>

<br>

### `[ 01 // SYSTEM_OVERVIEW ]`

Computer Science undergraduate in Brazil transitioning from backend engineering into **safety-critical flight software, formal verification, and bare-metal embedded systems**. 

I don't just write code that compiles—I engineer deterministic systems backed by formal proofs, strict static contracts, and aerospace assurance standards (**DO-178C**, **DO-333**, **DO-254**).

```text
+-------------------------------------------------------------------------+
| FLIGHT_DECK // OPERATIONAL PROFILE                                      |
+-------------------------------------------------------------------------+
| > PRIMARY DOMAIN   : Flight Control Laws, Collision Avoidance, SecBoot  |
| > ASSURANCE FOCUS  : Formal Verification (GNATprove), Zero-RTE Proofs   |
| > HARDWARE TARGETS : Bare-Metal MCUs, FPGA/VHDL Co-Sim, MIL-STD-1553    |
| > DAYTIME ENGINE   : Distributed Backends (TypeScript, NestJS, Postgres)|
+-------------------------------------------------------------------------+
[ 02 // ACTIVE_SUBSYSTEMS ]SUBSYSTEMDESIGNATIONASSURANCE / STACKARCHITECTURE & OBJECTIVEREPOFSACFlight Stability Augmentation ComputerSPARK 2014 Ada 2012DO-178C DAL-A DO-333Core stability augmentation control laws with mathematically proven absence of run-time errors via gnatprove contracts.SRC ↗TCAS-IITraffic Alert & Collision AvoidanceSPARK Ada C11DO-178C DAL-B UnityDual-language architecture pairing formally verified TA/RA resolution logic with a deterministic C11 hardware driver layer.SRC ↗CERBERUSCryptographic Secure Boot ChainC11 VHDL GHDLSHA-256 MonocypherBare-metal root-of-trust bring-up, firmware signature verification, and hardware-level simulation.SRC ↗MODULESPECIFICATIONSTACKMIL-STD-1553Avionics serial data bus controller/terminal protocol implementation & SDP baselinesC11 SPARK AdaTHERAC-25 SIMControl architecture reconstruction analyzing shared-state race conditions & overflow faultsC11 ConcurrencyINTEGRATED AVIONICSSystems engineering monorepo spanning ARP4754B/4761A, DO-254, and DO-326ASystems Eng AdaCPU EMU + RTOSDeterministic real-time kernel and custom instruction-set emulatorC RustBIRDFLU / BIRDCAGELow-level host intrusion detection, packet filtering, and firewall suiteC Linux[ 03 // TOOLCHAIN_&_VERIFICATION_MATRIX ]YAMLSAFETY_CRITICAL_&_SYSTEMS:
  languages:   [Ada 2012, SPARK 2014, C11 (-Wall -Wextra -Werror), C++, Rust, VHDL]
  toolchains:  [GNAT Native, Alire (alr), GPRbuild, GNATprove, GHDL, Unity Test]
  environment: [Linux, WSL2, MINGW64, Bare-Metal, GitHub Actions CI]

BACKEND_&_INFRASTRUCTURE:
  languages:   [TypeScript, Node.js, Python, SQL, Bash]
  frameworks:  [NestJS, Next.js, React]
  data_&_ops:  [PostgreSQL, Redis, Docker]
[ 04 // TELEMETRY_READOUT ][ 05 // COMMS_LINK ]
