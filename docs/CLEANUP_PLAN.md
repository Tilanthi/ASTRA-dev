# ASTRA Directory Cleanup Plan

## Current Root Directory Structure

### Keep in Root (User Specified)
- ✅ W3_HGBS_filaments/ - Filament research data
- ✅ filament_frag_analysis/ - Filament fragmentation analysis
- ✅ athena_mhd_results/ - MHD simulation results
- ✅ athena_mhd_results_v2/ - MHD simulation results v2
- ✅ User_Manual/ - User documentation

### Keep in Root (Core ASTRA)
- ✅ CLAUDE.md - Project documentation
- ✅ README.md - Project README
- ✅ requirements.txt - Python dependencies
- ✅ LICENSE - License file
- ✅ astra_core/ - Legacy cognitive framework (keep as-is)
- ✅ astra_live_backend/ - Active system (keep as-is)
- ✅ paper/ - RASTI paper
- ✅ figures/ - Paper figures
- ✅ config/ - System configuration
- ✅ docs/ - Documentation
- ✅ data/ - Data files

### Keep in Root (Tests)
- ✅ test_*.py - Test files
- ✅ tests/ - Test directory

### Keep in Root (Databases - Runtime)
- ✅ astra_discoveries.db - Main discovery database (runtime, in .gitignore)
- ✅ astra_discoveries_palace/ - GraphPalace knowledge graph (runtime, in .gitignore)
- ✅ astra.log - Runtime log
- ✅ astra_server.log - Server log
- ✅ .astra_server.pid - Server PID file

### Move to astra_core/data/
- 🔄 hypotheses/ - Hypothesis storage (move to astra_core/data/hypotheses)
- 🔄 knowledge/ - Knowledge base (move to astra_core/data/knowledge)
- 🔄 self_evolution/ - Self-evolution code (move to astra_core/self_evolution)
- 🔄 memory/ - Memory storage (move to astra_core/data/memory)
- 🔄 pipeline/ - Analysis pipeline (move to astra_core/pipeline)
- 🔄 logs/ - Log files (move to astra_core/data/logs)
- 🔄 astra_state/ - State files (move to astra_core/data/state)
- 🔄 astra-live/ - Dashboard HTML (move to astra_core/dashboard)
- 🔄 autotunnel_viz/ - Visualization (move to astra_core/data/autotunnel_viz)

### Delete (Old/Temporary Files)
- ❌ astra-rasti-v2.* - LaTeX compilation artifacts
- ❌ astra-rasti.* - LaTeX compilation artifacts
- ❌ supplement.* - LaTeX compilation artifacts
- ❌ *.aux, *.bbl, *.blg, *.out, *.toc, *.log - LaTeX artifacts
- ❌ texput.log - LaTeX log
- ❌ astra_discoveries.db.backup_* - Old backup files
- ❌ astra_knowledge.db - Old database
- ❌ astra_metacognition.db - Old database
- ❌ astra_agent_expertise.db - Old database
- ❌ astra_live_dashboard.html - Old dashboard file
- ❌ dashboard_connections_additions.html - Old dashboard file
- ❌ create_broken_ref_stubs.py - Stub creation script (temporary)
- ❌ create_remaining_stubs.py - Stub creation script (temporary)
- ❌ create_stub_modules.py - Stub creation script (temporary)
- ❌ fix_parse_errors.py - Old fix script
- ❌ fix_syntax_errors.py - Old fix script
- ❌ apply_license.py - License application script (temporary)
- ❌ init_hypotheses.py - Init script (temporary)
- ❌ install_graphpalace.py - Install script (temporary)
- ❌ migrate_to_graphpalace.py - Migration script (temporary)
- ❌ sync_discoveries_to_graphpalace.py - Migration script (temporary)
- ❌ astra_autonomous_agent.py - Old autonomous agent (moved to astra_live_backend)
- ❌ continuous_discovery_daemon.py - Old daemon (moved to astra_live_backend)
- ❌ restart_astra.py - Old restart script (temporary)
- ❌ reproduce.py - Can be moved to astra_core/
- ❌ generate_supplement.py - Can be moved to paper/
- ❌ autotunnel_viz/ scripts - Can be organized

### Keep in Root (Documentation - Review)
- 📝 COGNITIVE_ARCHITECTURE.md - Architecture doc (keep or move to docs/)
- 📝 EXPERIMENT_DESIGN_ARCHITECTURE.md - Architecture doc (keep or move to docs/)
- 📝 UNIFIED_DISCOVERY_ARCHITECTURE.md - Architecture doc (keep or move to docs/)
- 📝 GITHUB_PUSH_ISSUE.md - GitHub issue (delete or move to docs/)
- 📝 RESTART_COMPLETE.md - Old status (delete)
- 📝 ASTROPHYSICS_VERIFIER_IMPLEMENTATION.md - Implementation doc (keep or move to docs/)
- 📝 ATLAS_INTEGRATION*.md - Integration docs (keep or move to docs/)
- 📝 GRAPH_PALACE_FIX_REPORT.md - Fix report (delete or move to docs/)
- 📝 graphpalace_bug_report.md - Bug report (delete)
- 📝 DASHBOARD_*.md - Dashboard status docs (delete)
- 📝 test_*.py - Keep test files in root

### Review/Keep (Scripts)
- 📝 visualize_autotunnels.py - Visualization script (keep or move to astra_core/)
- 📝 auto_viz_autotunnels.py - Visualization script (keep or move to astra_core/)
- 📝 create_cross_domain_discoveries.py - Test script (keep or move to tests/)
- 📝 run_verification_workflow.py - Verification script (keep or move to tests/)

## Path Updates Required

After moving folders, update these hardcoded paths:
1. `astra_live_backend/generate_dashboard.py`: OUTPUT_PATH = "astra-live/index.html"
2. `astra_live_backend/server.py`: DASHBOARD_DIR = Path("astra-live")
3. Any scripts referencing `hypotheses/`, `knowledge/`, `memory/`, `pipeline/`

## Testing Plan

1. Stop ASTRA server
2. Move folders
3. Update paths
4. Run pytest on astra_live_backend/
5. Start ASTRA server
6. Test dashboard
7. Test discovery cycles
8. Fix any issues
9. Repeat until clean
