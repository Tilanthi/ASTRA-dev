# Bug Report: Module resolution error in gp-palace prevents compilation

## Summary
GraphPalace fails to compile due to unresolved module `search` in `gp-palace/src/palace.rs`, despite the module being correctly declared in `gp-palace/src/lib.rs`. This prevents building the Python bindings and using the library.

## Environment
- **Rust version**: rustc 1.91.0 (f8297e351 2025-10-28)
- **Cargo version**: 1.91.0 (ea2d97820 2025-10-10)
- **Python version**: 3.14.2
- **Operating System**: macOS (Darwin 25.4.0, aarch64)
- **GraphPalace commit**: c9299e37a (master branch, latest)
- **Build command**: `maturin develop --release` with `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1`

## Steps to Reproduce
```bash
# 1. Clone repository
git clone https://github.com/web3guru888/GraphPalace.git
cd GraphPalace/rust/gp-python

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install maturin
pip install maturin

# 4. Build with Python 3.14 compatibility flag
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop --release
```

## Error Messages
```
error[E0433]: failed to resolve: use of unresolved module or unlinked crate `search`
   --> gp-palace/src/palace.rs:942:24
    |
942 |     ) -> Result<Option<search::DuplicateMatch>> {
    |                        ^^^^^^ use of unresolved module or unlinked crate `search`
    |
help: to make use of source file gp-palace/src/search.rs, use `mod search` in this file to declare the module
   --> gp-palace/src/lib.rs:9:1
    |
9  + mod search;
    |
help: consider importing this module
    |
6  + use crate::search;
    |

error[E0433]: failed to resolve: use of unresolved module or unlinked crate `search`
   --> gp-palace/src/palace.rs:947:22
    |
947 |             .map(|r| search::DuplicateMatch {
    |                      ^^^^^^ use of unresolved module or unlinked crate `search`
    |
help: to make use of source file gp-palace/src/search.rs, use `mod search` in this file to declare the module
   --> gp-palace/src/lib.rs:9:1
    |
9  + mod search;
    |
help: consider importing this module
    |
6  + use crate::search;
    |

error: could not compile `gp-palace` (lib) due to 2 previous errors
```

## Investigation

### Verified that module IS declared:
```bash
$ cat gp-palace/src/lib.rs
//! `gp-palace` — Unified GraphPalace orchestrator.
// ...

pub mod export;
pub mod lifecycle;
pub mod palace;
pub mod search;  # ← Module is declared here

// Re-export primary public types.
pub use export::{ImportMode, ImportStats, PalaceExport};
pub use lifecycle::{ColdSpot, HotPath, KgRelationship, PalaceStatus};
pub use palace::GraphPalace;
pub use search::{DuplicateMatch, SearchResult};  # ← Types are re-exported
```

### Verified that search.rs EXISTS:
```bash
$ ls -la gp-palace/src/search.rs
-rw-r--r-- 1 user staff 3.2K Dec 13 10:23 gp-palace/src/search.rs
```

### Verified imports in palace.rs:
```rust
// Line 21 in palace.rs
use crate::search::{PheromoneBooster, SearchResult};

// Lines 942, 947 where error occurs
search::DuplicateMatch  // ← Compiler says this is unresolved
```

## Attempted Fixes
1. **Clean build**: `cargo clean && cargo build --release` - Same error
2. **Direct cargo build**: `cargo build --release -p gp-palace` - Same error
3. **Different build directories**: Tried building from `rust/` and `rust/gp-python` - Same error
4. **Updated Cargo.lock**: Deleted and regenerated - Same error

## Expected Behavior
The `search` module should resolve correctly since:
1. It is declared as `pub mod search;` in `gp-palace/src/lib.rs`
2. The file `gp-palace/src/search.rs` exists
3. The types are re-exported: `pub use search::{DuplicateMatch, SearchResult};`
4. Other modules (`export`, `lifecycle`, `palace`) follow the same pattern and work fine

## Actual Behavior
Rust compiler cannot resolve the `search` module, despite all evidence that it should be resolvable. This suggests either:
- A circular dependency issue
- A module visibility problem
- A Cargo workspace configuration issue
- A bug in the Rust compiler (unlikely)

## Impact
- **Cannot build Python bindings** - blocks Python integration
- **Cannot use GraphPalace** - library is completely non-functional
- **Claims of "production-ready"** are questionable - basic compilation fails

## Additional Context
The README claims:
- "All 10 phases complete — 13 Rust crates, 694 tests, 24,070 LOC, zero failures"
- "Production-ready with HNSW vector index, full CLI, MCP auth, and crash-safe persistence"

However, if the code cannot compile, it's unclear how:
1. Tests could pass (tests are usually run after compilation)
2. The CLI could be functional (requires compiled binaries)
3. Production use is possible (code must compile to deploy)

## Possible Root Causes
1. **Recent regression** - The latest commit c9299e37a mentions "search fix" but may have introduced this bug
2. **Workspace configuration issue** - The `Cargo.toml` workspace structure may not include `gp-palace` correctly
3. **Module ordering issue** - There may be a circular dependency between `palace.rs` and `search.rs`
4. **Test artifacts only** - The repository may have test binaries but source doesn't compile

## Suggested Next Steps
1. Check if `gp-palace/Cargo.toml` correctly declares dependencies
2. Verify no circular imports between `palace.rs` and `search.rs`
3. Try building with Rust stable vs Rust nightly
4. Review commit c9299e37a changes to `search.rs` and `palace.rs`
5. If tests exist, check how they're being run (possibly pre-compiled binaries?)

## Workaround (for maintainers)
If this is a workspace configuration issue, consider:
```toml
# In gp-palace/Cargo.toml, ensure:
[lib]
name = "gp_palace"
path = "src/lib.rs"

[dependencies]
# ... other dependencies ...
```

## Priority
**High** - This is a blocker that prevents any use of GraphPalace. The library cannot be compiled, built, or deployed.

## Contact
For additional information or reproduction steps, please contact the original reporter.
