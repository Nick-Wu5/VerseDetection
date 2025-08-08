# Bible Verse Detection Process Flowchart

```mermaid
flowchart TD
    A[📖 Bible Page Image] --> B[🔍 Google Vision OCR]
    B --> C[📄 Raw OCR Text]

    C --> D[🎯 Verse Detection Process]

    D --> E[📝 Split Text into Lines]
    E --> F[🔍 Extract Verse Numbers]

    F --> G{Verse Number Found?}
    G -->|Yes| H[📋 Start New Verse Block]
    G -->|No| I{Is Continuation?}

    I -->|Yes| J[📄 Add to Current Verse]
    I -->|No| K[💾 Save Current Verse]

    H --> L[📊 Create VerseBlock Object]
    J --> M[🔄 Continue Processing]
    K --> N[🔄 Continue Processing]

    L --> O[🎯 Confidence Calculation]
    M --> E
    N --> E

    O --> P[📈 Content Quality Assessment]

    P --> Q[🔍 Multi-Factor Validation]

    Q --> R[📊 Content Completeness]
    Q --> S[🔤 Character Quality]
    Q --> T[🎲 Entropy Analysis]
    Q --> U[🖨️ OCR Artifact Detection]
    Q --> V[🔗 Page Boundary Detection]

    R --> W[📏 Word Count & Length]
    S --> X[📊 Readable Character Ratio]
    T --> Y[🎯 Shannon Entropy]
    U --> Z[🚫 Artifact Patterns]
    V --> AA[🔍 Fragment Detection]

    W --> BB[📊 Completeness Score]
    X --> CC[📊 Character Quality Score]
    Y --> DD[📊 Entropy Score]
    Z --> EE[📊 OCR Artifact Penalty]
    AA --> FF[📊 Page Boundary Penalty]

    BB --> GG[🎯 Combined Quality Score]
    CC --> GG
    DD --> GG
    EE --> GG
    FF --> GG

    GG --> HH[🎯 Final Confidence Score]

    HH --> II{Confidence ≥ Threshold?}
    II -->|Yes| JJ[✅ High Confidence Verse]
    II -->|No| KK[⚠️ Low Confidence Verse]

    JJ --> LL[📋 Add to High Confidence List]
    KK --> MM[📋 Add to Low Confidence List]

    LL --> NN[📊 Generate Statistics]
    MM --> NN

    NN --> OO[📈 Final Results]

    OO --> PP[🎯 Relevant Verses Identified]

    %% Detailed sub-processes
    subgraph "Verse Number Patterns"
        F1[🔢 Standard Numbers: 1, 2, 3]
        F2[📖 Chapter:Verse: 1:1, 2:3]
        F3[📚 Book Format: Psalm 139:1]
        F4[🔤 Roman Numerals: I, II, III]
        F5[📑 Chapter Format: Chapter 1]
    end

    F --> F1
    F --> F2
    F --> F3
    F --> F4
    F --> F5

    subgraph "Content Quality Factors"
        R1[📊 Word Count ≥ 8: 0.3 pts]
        R2[📊 Word Count ≥ 4: 0.2 pts]
        R3[📊 Word Count ≥ 2: 0.1 pts]
        R4[📏 Avg Word Length ≥ 4: 1.0x]
        R5[📏 Avg Word Length ≥ 3: 0.8x]
    end

    W --> R1
    W --> R2
    W --> R3
    W --> R4
    W --> R5

    subgraph "OCR Artifact Detection"
        Z1[🚫 >30% Repeated Characters]
        Z2[🚫 >40% Non-Alphabetic]
        Z3[🚫 Short Repeated Patterns]
        Z4[🚫 Unusual Character Distribution]
    end

    Z --> Z1
    Z --> Z2
    Z --> Z3
    Z --> Z4

    subgraph "Page Boundary Detection"
        AA1[🔍 ≤3 Words]
        AA2[🔍 Number + Short Word: "2 When"]
        AA3[🔍 <20 Chars After Number]
        AA4[🔍 <6 Words No Ending]
        AA5[🔍 <40 Chars Cut-off]
    end

    AA --> AA1
    AA --> AA2
    AA --> AA3
    AA --> AA4
    AA --> AA5

    subgraph "Confidence Scoring"
        HH1[📏 Content Length > 20: +0.3]
        HH2[📖 Chapter:Verse Format: +0.4]
        HH3[🔢 Simple Verse Number: +0.3]
        HH4[📚 Book Names: +0.5]
        HH5[✅ Valid Verse Number: +0.3]
        HH6[🎯 Content Quality: ×0.4]
        HH7[🔗 Page Boundary: -0.5]
    end

    HH --> HH1
    HH --> HH2
    HH --> HH3
    HH --> HH4
    HH --> HH5
    HH --> HH6
    HH --> HH7

    %% Styling
    classDef startEnd fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef validation fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class A,PP startEnd
    class B,C,D,E,F,H,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,AA,BB,CC,DD,EE,FF,GG,HH,LL,MM,NN process
    class G,I,II decision
    class R1,R2,R3,R4,R5,Z1,Z2,Z3,Z4,AA1,AA2,AA3,AA4,AA5,HH1,HH2,HH3,HH4,HH5,HH6,HH7 validation
    class JJ,KK,OO output
```

## Process Overview

### **Phase 1: Image Processing**

1. **Bible Page Image** → **Google Vision OCR** → **Raw OCR Text**

### **Phase 2: Verse Detection**

1. **Split Text into Lines**
2. **Extract Verse Numbers** using multiple patterns:

   - Standard numbers (1, 2, 3)
   - Chapter:verse format (1:1, 2:3)
   - Book format (Psalm 139:1)
   - Roman numerals (I, II, III)
   - Chapter format (Chapter 1)

3. **Create Verse Blocks**:
   - Start new verse when verse number found
   - Continue current verse for continuations
   - Save verse when new verse or end reached

### **Phase 3: Content Quality Assessment**

1. **Content Completeness**:

   - Word count scoring (≥8: 0.3, ≥4: 0.2, ≥2: 0.1)
   - Word length quality multiplier (≥4: 1.0x, ≥3: 0.8x)

2. **Character Quality**:

   - Readable character ratio (≥80%: 0.2, ≥60%: 0.1)

3. **Entropy Analysis**:

   - Shannon entropy calculation
   - Normalized to 0-1 range

4. **OCR Artifact Detection**:

   - > 30% repeated characters
   - > 40% non-alphabetic
   - Short repeated patterns
   - Unusual character distribution

5. **Page Boundary Detection**:
   - ≤3 words
   - Number + short word patterns
   - <20 chars after numbers
   - <6 words without ending
   - <40 chars cut-off

### **Phase 4: Confidence Scoring**

1. **Content Length** (>20: +0.3)
2. **Verse Number Format** (Chapter:verse: +0.4, Simple: +0.3, Book: +0.5)
3. **Verse Number Validation** (Valid: +0.3)
4. **Content Quality** (×0.4 weight)
5. **Fragment Penalties** (Page boundary: -0.5)

### **Phase 5: Final Filtering**

1. **Confidence Threshold** (≥0.5 for high confidence)
2. **High Confidence Verses** → **Relevant Verses**
3. **Low Confidence Verses** → **Filtered Out**

### **Phase 6: Results Generation**

1. **Statistics** (total verses, high confidence, quality scores)
2. **Final Results** with identified relevant verses
