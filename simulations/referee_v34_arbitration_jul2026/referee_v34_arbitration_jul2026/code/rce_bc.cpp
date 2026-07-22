}

// ═════════════════════════════════════════════════════════════════════════════
//  USER BOUNDARY CONDITION FUNCTIONS
//  All four implement: density floor = max(face_rho, p_ext_ratio)
//                      velocity / B-field: zero gradient (copy from face)
// ═════════════════════════════════════════════════════════════════════════════

// ── inner_x2: ghost cells at j = js-1, js-2, ..., js-ngh ───────────────────
void InnerX2_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int k = ks; k <= ke; ++k) {
        for (int n = 1; n <= ngh; ++n) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, k, js-n, i) = std::max(prim(IDN, k, js, i), g_p_ext);
                prim(IVX, k, js-n, i) = prim(IVX, k, js, i);
                prim(IVY, k, js-n, i) = prim(IVY, k, js, i);
                prim(IVZ, k, js-n, i) = prim(IVZ, k, js, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f: face-centered in x1 (i has extra +1 face)
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(k, js-n, i) = b.x1f(k, js, i);

        // x2f: face-centered in x2; ghost faces at js-n (boundary face = js)
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x2f(k, js-n, i) = b.x2f(k, js, i);

        // x3f: face-centered in x3 (k has extra +1 face)
        for (int k = ks; k <= ke + 1; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x3f(k, js-n, i) = b.x3f(k, js, i);
    }
}

// ── outer_x2: ghost cells at j = je+1, je+2, ..., je+ngh ───────────────────
void OuterX2_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int k = ks; k <= ke; ++k) {
        for (int n = 1; n <= ngh; ++n) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, k, je+n, i) = std::max(prim(IDN, k, je, i), g_p_ext);
                prim(IVX, k, je+n, i) = prim(IVX, k, je, i);
                prim(IVY, k, je+n, i) = prim(IVY, k, je, i);
                prim(IVZ, k, je+n, i) = prim(IVZ, k, je, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(k, je+n, i) = b.x1f(k, je, i);

        // x2f: last active face = je+1; ghost faces at je+1+n
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x2f(k, je+1+n, i) = b.x2f(k, je+1, i);

        // x3f
        for (int k = ks; k <= ke + 1; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x3f(k, je+n, i) = b.x3f(k, je, i);
    }
}

// ── inner_x3: ghost cells at k = ks-1, ks-2, ..., ks-ngh ───────────────────
void InnerX3_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int n = 1; n <= ngh; ++n) {
        for (int j = js; j <= je; ++j) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, ks-n, j, i) = std::max(prim(IDN, ks, j, i), g_p_ext);
                prim(IVX, ks-n, j, i) = prim(IVX, ks, j, i);
                prim(IVY, ks-n, j, i) = prim(IVY, ks, j, i);
                prim(IVZ, ks-n, j, i) = prim(IVZ, ks, j, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(ks-n, j, i) = b.x1f(ks, j, i);

        // x2f: face-centered in x2 (j has extra +1 face)
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je + 1; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x2f(ks-n, j, i) = b.x2f(ks, j, i);

        // x3f: ghost faces at ks-n (boundary face = ks)
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x3f(ks-n, j, i) = b.x3f(ks, j, i);
    }
}

// ── outer_x3: ghost cells at k = ke+1, ke+2, ..., ke+ngh ───────────────────
void OuterX3_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int n = 1; n <= ngh; ++n) {
        for (int j = js; j <= je; ++j) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, ke+n, j, i) = std::max(prim(IDN, ke, j, i), g_p_ext);
                prim(IVX, ke+n, j, i) = prim(IVX, ke, j, i);
                prim(IVY, ke+n, j, i) = prim(IVY, ke, j, i);
                prim(IVZ, ke+n, j, i) = prim(IVZ, ke, j, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(ke+n, j, i) = b.x1f(ke, j, i);

        // x2f
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je + 1; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x2f(ke+n, j, i) = b.x2f(ke, j, i);

        // x3f: last active face = ke+1; ghost faces at ke+1+n
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x3f(ke+1+n, j, i) = b.x3f(ke+1, j, i);
    }
}
