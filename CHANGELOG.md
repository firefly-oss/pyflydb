# Changelog

All notable changes to pyFlyDb will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-07

### Added
- Initial stable release of pyFlyDb
- Full binary protocol implementation for FlyDB
- DB-API 2.0 compliant interface
- Connection management with authentication support
- Cursor implementation with all fetch methods
- Transaction support (BEGIN, COMMIT, ROLLBACK)
- Parameterized queries (positional and named parameters)
- Context manager support for automatic resource cleanup
- Thread-safe connection handling
- Ping/health check functionality
- Server information retrieval
- Comprehensive exception hierarchy
- DSN connection string parsing (URI and key-value formats)
- Enhanced result parsing for FlyDB response format
- Type adapters with Pydantic integration
- Row objects with multiple access methods
- Full copyright headers and Apache 2.0 licensing
- Extensive documentation and examples
- Professional package structure with pyproject.toml
- Comprehensive integration test suite (20 tests)

### Protocol Features
- Magic byte validation (0xFD)
- Protocol version checking (0x01)
- Message type encoding/decoding
- Header validation and error handling
- Support for all core message types:
  - AUTH / AUTH_RESULT
  - QUERY / QUERY_RESULT  
  - PING / PONG
  - BEGIN_TX / COMMIT_TX / ROLLBACK_TX
  - GET_SERVER_INFO / SESSION_RESULT
  - ERROR messages

### Documentation
- Comprehensive README with usage examples
- Getting Started guide
- Architecture diagrams
- API documentation
- Code examples (basic_usage.py, debug_protocol.py)
- Installation instructions
- Performance tips

### Testing
- All 20 integration tests passing against FlyDB 1.0.0
- Connection and authentication verified
- Query execution (CREATE, INSERT, SELECT, UPDATE, DELETE)
- Transaction management (COMMIT, ROLLBACK)
- Parameterized queries (positional and named)
- DSN parsing
- Type adapters and Row objects
- Result parser
- Binary protocol communication confirmed

## Known Limitations

- Connection pooling: Planned for future release
- Prepared statements: Protocol support implemented, pending full integration
- Async support: Planned for future major version
- SSL/TLS: Not yet implemented
- Server-side cursors: Not yet implemented

## [Unreleased]

### Planned
- Connection pooling implementation
- Async/await support (asyncio)
- Prepared statement full integration
- Server-side cursor support
- Batch operation optimizations
- SSL/TLS support

---

**Note**: This is the first stable release (1.0.0) of pyFlyDb. The API is considered stable 
but may receive enhancements in future versions. Feedback and contributions are welcome!
