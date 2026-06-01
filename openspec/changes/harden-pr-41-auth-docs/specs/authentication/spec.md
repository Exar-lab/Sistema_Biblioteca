# Authentication Specification

## Purpose

Defines the system's requirements and behavior for JWT-based authentication, user identification, and role-based authorization policy. Includes handling of malformed tokens and strict role validation.

## Requirements

### Requirement: Token Parsing and Sub Claim Validation

The system MUST validate the presence and integrity of the `sub` claim in the provided JWT token. If the claim is malformed, missing, or cannot be parsed, the system SHALL reject the request with a controlled 401 Unauthorized status rather than causing an internal server error (500).

#### Scenario: Valid JWT Token

- GIVEN a request with a valid JWT token containing a well-formed `sub` claim
- WHEN the system parses the token to authenticate the user
- THEN the system parses the user ID successfully
- AND proceeds with the authentication flow

#### Scenario: Missing Sub Claim

- GIVEN a request with a JWT token that lacks a `sub` claim
- WHEN the system attempts to extract the user ID
- THEN the system returns a 401 Unauthorized response
- AND the error details indicate credentials could not be validated

#### Scenario: Malformed Token

- GIVEN a request with a structurally invalid or malformed JWT token
- WHEN the system attempts to decode the token
- THEN the system handles the parsing exception
- AND returns a 401 Unauthorized response instead of a 500 Internal Server Error

### Requirement: Centralized Role-Based Policy

The system MUST authorize users against a centralized, normalized role policy (e.g., using constants or enums) rather than relying on bare string literal matches.

#### Scenario: Authorized Admin Access

- GIVEN an authenticated user with an "Admin" role (normalized)
- WHEN the user attempts to access an administrative endpoint
- THEN the system evaluates the role against the centralized policy
- AND grants access to the endpoint

#### Scenario: Unauthorized Role Access

- GIVEN an authenticated user with a "User" role
- WHEN the user attempts to access an administrative endpoint
- THEN the system evaluates the role against the centralized policy
- AND returns a 403 Forbidden response

### Requirement: Operational Documentation

The system's `README.md` MUST include documentation on JWT requirements (such as configuring `SECRET_KEY`), authentication flows, and troubleshooting steps for developers.

#### Scenario: Developer Setup

- GIVEN a new developer setting up the project
- WHEN they read the `README.md`
- THEN they find explicit instructions on how to configure the `SECRET_KEY` and troubleshoot JWT authentication issues
