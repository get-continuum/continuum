export class ContinuumError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContinuumError";
  }
}

export type HttpErrorInit = {
  statusCode: number;
  message: string;
  url?: string;
  responseText?: string;
};

export class HttpError extends ContinuumError {
  readonly statusCode: number;
  readonly url: string | undefined;
  readonly responseText: string | undefined;

  constructor(init: HttpErrorInit) {
    super(init.message);
    this.name = "HttpError";
    this.statusCode = init.statusCode;
    this.url = init.url;
    this.responseText = init.responseText;
  }
}

export class AuthError extends HttpError {
  constructor(init: HttpErrorInit) {
    super(init);
    this.name = "AuthError";
  }
}

export class ResolveError extends HttpError {
  constructor(init: HttpErrorInit) {
    super(init);
    this.name = "ResolveError";
  }
}

