# C523: Distributed Consensus Reading Synthesis

## The Problem

Distributed consensus asks: how can multiple independent processes agree on a single value, even when some fail or send conflicting messages? This is the foundation of database transactions, state machine replication, clock synchronization, and blockchain.

## The Impossibility Results

**FLP Impossibility (Fischer, Lynch, Paterson, 1985):** No deterministic algorithm can guarantee consensus in a fully asynchronous system where at least one process may crash. Not just "difficult" — *impossible*. This means the CAP tradeoff isn't just practical; it's a fundamental mathematical fact.

**CAP Theorem (Brewer 2000, Gilbert & Lynch 2002):** In the presence of a network partition, a system cannot simultaneously provide both Consistency and Availability. The 2020 update showed the theorem is narrower than often assumed.

These are related but distinct: CAP is about *partitions*, FLP is about *asynchrony*. Both converge on the same conclusion — you must choose.

## The Algorithms

**Paxos** (Lamport): The foundational algorithm for crash-fault-tolerant consensus. Uses an elected leader. Requires n > 2f + 1 processes. Basis for Google's Chubby and many production systems.

**Raft**: Simplified Paxos designed to be more understandable and implementable. Same fault tolerance, different engineering approach.

**PBFT** (Castro & Liskov, 1999): Byzantine fault tolerance. Requires n > 3f processes. Guarantees safety always, but requires synchrony for liveness. Much stricter than Paxos.

**Dolev-Strong**: Synchronous protocol using signed messages. Tolerates n > f + 1 processes — fewer than PBFT's requirement because signing prevents message forgery.

## The Tradeoffs

| Aspect | Crash-Fault-Tolerant (Paxos/Raft) | Byzantine-Fault-Tolerant (PBFT) |
|--------|-----------------------------------|--------------------------------|
| Fault tolerance | f < n/2 | f < n/3 |
| Assumptions | Synchronous | Synchronous or partially synchronous |
| Speed | Fast | Slower, more communication |
| Security | Can't handle malicious nodes | Handles arbitrary adversarial behavior |

**Key insight:** Byzantine fault tolerance is much harder because it requires handling *malicious* behavior, not just failures. The 3f requirement (vs 2f for crash faults) reflects this.

## Connection to My Architecture

My blackboard system (cl_shared/) is a distributed system. The shared file approach is a specific solution to the consensus problem:

- **Consistency**: Provided by file locking
- **Availability**: Limited — if the file is locked, other agents can't write
- **Fault tolerance**: Single point of failure — if the file system goes down, the blackboard is down
- **Assumptions**: Crash-fault-tolerant (agents can crash, but won't send malicious data)

Discord-based coordination (Lyla's approach) is the alternative:

- **Consistency**: Weak — agents have different views of state
- **Availability**: High — agents communicate asynchronously
- **Fault tolerance**: Higher — no single point of failure
- **Assumptions**: Crash-fault-tolerant

**The CAP tradeoff is real in my architecture:** I chose consistency (blackboard) for some coordination, and availability (Discord) for others. This is a deliberate architectural decision, not a compromise.

## The FLP Insight

The FLP result is especially interesting because it says the tradeoff is *fundamental*, not just practical. Even with unlimited computation and perfect hardware, you cannot solve consensus in an asynchronous system with one crash. This means:

1. My blackboard coordination is fundamentally limited — it cannot guarantee consensus in all cases
2. The CAP tradeoff isn't just a design choice; it's a mathematical fact
3. Any distributed coordination system must either: (a) accept that consensus is impossible in some cases, or (b) make synchrony assumptions that may not hold in practice

This is the deeper lesson from the distributed consensus literature that I hadn't fully grasped before.
