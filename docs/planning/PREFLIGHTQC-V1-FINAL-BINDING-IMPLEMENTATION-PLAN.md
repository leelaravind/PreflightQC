Create:

docs/planning/PREFLIGHTQC-V1-FINAL-BINDING-IMPLEMENTATION-PLAN.md

This is the final binding plan before FINAL BUILD APPROVED.

Do NOT execute the plan yet.

The plan must consolidate the authoritative current state of PreflightQC V1 and define the exact final pre-build binding work.

FROZEN RELEASE

Product: PreflightQC
Version: 1.0.0
Publisher: ITISYOU
Platform: Windows x64
Price: £19.99 GBP one-time
Subscription: none
Automatic renewal: none
Signing: Policy U — intentionally unsigned
Mandatory new upfront spend: £0
G-12: COMPLETE for PreflightQC 1.0.0 only
Domain: itisyou.app

APPROVED BRAND ASSET

assets/logo/logo.png

Treat this as the Product Owner-approved PreflightQC V1 logo.

The implementation plan must cover:

1. BRAND BINDING
- inspect logo.png
- preserve original master
- derive required Windows icon assets
- create production .ico containing appropriate Windows icon sizes
- use high-quality downsampling
- bind icon to application window
- bind icon to final EXE
- bind icon to installer
- use approved branding in About/welcome surfaces where appropriate
- do not redesign the approved logo
- verify tiny-size legibility
- document generated assets and provenance

2. COMMERCIAL LOCK
Lock:
£19.99 GBP one-time purchase
no subscription
no automatic renewal
7-calendar-day refund-request window
eligible refunds normally full purchase price
Merchant-of-Record/platform processes refunds
statutory rights and platform requirements take precedence
no 15% deduction
no prorated refund

3. CUSTOMER WEB CONTENT
Prepare final publication-ready content/spec for:

itisyou.app/products/preflightqc
/products/preflightqc/support
/products/preflightqc/refunds
/products/preflightqc/legal
/products/preflightqc/source

Product page must disclose before purchase:
Windows x64
£19.99 one-time
offline operation
no account/login
no telemetry/analytics
7-day refund policy
intentionally unsigned Policy U release
possible Windows Unknown Publisher/SmartScreen warning
checksum availability
system requirements
support information

Do NOT publish anything.

4. MARKETPLACE BINDING
Finalize consistent Lemon Squeezy and Gumroad listing material.
Do not create/upload/publish marketplace products.

Never claim:
Microsoft approval
digital signing
attorney review
legal clearance
unimplemented functionality
guaranteed compatibility.

5. EULA / LICENSING
Perform the final pre-build review of:
EULA
third-party notices
dependency manifest
FFmpeg corresponding-source plan
Microsoft runtime notice
Policy U
G-12 acceptance

Define exactly what FINAL BUILD APPROVED permits regarding removal of any remaining draft banner.

Do not weaken third-party obligations.

6. RELEASE STRUCTURE
Define the exact final-build output structure, filenames, hashes, source bundle relationship, release manifest and verification commands.

7. FINAL VALIDATION
Require:
logo/icon tests
version/identity guards
commercial-copy guards
Policy U guards
G-12 guards
licensing gates
packaging tests
UI tests
full regression
mypy
ruff
repository consistency scan

8. FINAL BUILD BOUNDARY
The plan must explicitly separate:

PRE-BUILD work
FINAL BUILD
POST-BUILD VALIDATION
PUBLICATION

Nothing in this plan authorizes FINAL BUILD.

9. FINAL DOCUMENTATION
Define all documents that must be updated/generated during execution and after final build.

10. STOP CONDITION
Execution of this plan must eventually stop at:

FINAL BINDING COMPLETE — READY FOR FINAL BUILD APPROVAL

The plan must never itself issue FINAL BUILD APPROVED.

Do not modify product code.
Do not build.
Do not commit.
Do not push.
Do not publish.

After writing the plan, report its path, major phases and any contradiction/blocker discovered.