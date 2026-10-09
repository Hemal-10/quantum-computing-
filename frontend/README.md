# Quantum DNA Sequence Analyzer – Frontend

A scientific dashboard bridging classical bioinformatics and quantum computation using React 19, TypeScript, Tailwind CSS, and Recharts.

---

## Dashboard Sections

1. **Overview Dashboard**
   - Live backend connectivity status with ping control
   - Step-by-step computational architecture pipeline
   - Benchmark genomic presets (Sickle Cell Anemia HBB snippet, BRCA1 gene fragment, TATA Box promoter, EcoRI restriction site, and identical negative control)
   - Module navigation cards

2. **DNA Sequence Comparison**
   - Pairwise sequence inputs with nucleotide validation (`A`, `T`, `G`, `C`)
   - Real-time length mismatch alerts
   - Dual-track alignment viewer with color-coded nucleotide chips:
     - `A`: Emerald Green
     - `T`: Rose Red
     - `C`: Cyan Blue
     - `G`: Amber Gold
   - Pulsing mismatch indicators with 1-based biological coordinates

3. **Mutation Results Directory**
   - Summary metric cards (Sequence length, total mismatches, mutation percentage, quantum candidate map)
   - Detailed positional directory with transition vs. transversion biochemical classifications
   - One-click bridge button to load mutation positions directly into Grover Quantum Search

4. **Genomic Motif Search**
   - Search for regulatory elements, transcription factor binding sites, or restriction sites
   - Interactive sequence track highlighting matched motif windows
   - One-click bridge button to search motif match coordinates with Grover Quantum Search

5. **Qiskit Grover Search Engine**
   - Configurable candidate indices and marked target predicates
   - Shots slider (64 to 4,096)
   - Real-time qubit allocation and Hilbert space previews
   - Circuit metadata display: Search Qubits, Grover Iterations, Circuit Depth, and Empirical Success Rate
   - Interactive **Recharts** bar chart with:
     - Probability (%) and raw measurement shot counts toggle
     - Decoded indices $|x\rangle$ vs raw bitstrings toggle
     - Distinct radiant cyan/violet gradients for marked targets vs slate for unmarked states
     - Uniform probability baseline reference line
   - Simulator notice clarifying AerSimulator execution

6. **Classical vs Quantum Analysis**
   - Direct architectural and complexity comparison table ($O(N)$ vs $O(\sqrt{N})$, deterministic vs probabilistic, NISQ noise caveats)
   - Live empirical benchmark runner comparing execution latency, query steps, and accuracy on the active sequence
   - Scientific discussion on quantum advantage boundaries

---

## Development

```bash
# Install dependencies
npm install

# Run Vitest test suite
npm test

# Build for production
npm run build

# Start local development server (proxies /api to http://127.0.0.1:8000)
npm run dev
```
