# Security

This project contains specifications, an interface concept, and a local research lab with an intentional access-control flaw. It is not a trained security model or production assessment service.

The local HTTP assessment engine accepts only controller-issued lab grants bound to a tenant/project, exact literal-IP origin, approved accounts, and expiry. Reset/shutdown revoke grants. It does not accept arbitrary website targets or execute target-supplied scripts/instructions. Its local registry/storage and cooperative timers are prototype controls, not production isolation. See [assessment engine boundaries](docs/assessment-engine.md).

The lab binds only to 127.0.0.1 and uses synthetic data. Other local processes can reach it: loopback binding is not a container or OS sandbox. Do not expose it through public bind addresses, tunnels, or reverse proxies. Its reset and evaluator ground truth are deliberately unavailable through HTTP. See [lab instructions](labs/invoice/README.md).

Future execution must be restricted to systems the operator owns or is explicitly authorized to test. Domain ownership, scope, tenant isolation, credential handling, and tool policy are system controls, not responsibilities delegated to the model.

Do not place secrets or exploit details for an unpatched third-party system in public issues.

Repository administrators should enable GitHub private vulnerability reporting before accepting sensitive reports. If enabled, use the repository's Security tab to report a vulnerability privately. No separate security inbox is configured yet.
