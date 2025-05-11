import axios from "axios";

/**
 * Hypermedia API Client
 *
 * A utility for navigating hypermedia APIs that follow HATEOAS principles.
 * Allows for discovering and navigating through API controls, retrieving schemas,
 * and performing operations.
 */
class HypermediaClient {
  /**
   * Create a new HypermediaClient instance
   *
   * @param {string} baseUrl - Base URL of the API
   * @param {object} defaultHeaders - Default headers to include in all requests
   */
  constructor(defaultHeaders = {}) {
    this.baseUrl =
      import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/";
    this.defaultHeaders = {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...defaultHeaders,
    };
    this.currentResource = null;
    this.apiKey = localStorage.getItem("api-key");
    this.routes = null;

    // Initialize axios instance
    this.axios = axios.create({
      baseURL: this.baseUrl,
      headers: this.defaultHeaders,
    });

    // Add request interceptor to include API key if available
    this.axios.interceptors.request.use((config) => {
      if (this.apiKey) {
        config.headers["X-API-Key"] = this.apiKey;
      }
      return config;
    });
  }

  /**
   * Set the API key for future requests
   *
   * @param {string} apiKey - The API key to use
   */
  setApiKey(apiKey) {
    this.apiKey = apiKey;
    if (apiKey) {
      localStorage.setItem("api-key", apiKey);
    } else {
      localStorage.removeItem("api-key");
    }
  }

  /**
   * Navigate to the API root
   *
   * @returns {Promise<object>} The API root resource
   */
  async navigateToRoot() {
    try {
      const response = await this.axios.get("/api/");
      this.currentResource = response.data;

      // Store routes if available
      if (this.currentResource.available_routes) {
        this.routes = this.currentResource.available_routes;
      }

      return this.currentResource;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get an endpoint URL for a resource type and HTTP method
   *
   * @param {string} resourceType - The resource type (e.g., 'User', 'Group', 'Expense')
   * @param {string} method - The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE')
   * @param {object} params - Optional URL parameters (e.g., { user_id: 123 })
   * @returns {string|null} The endpoint URL or null if not found
   */
  getResourceEndpoint(resourceType, method, params = {}) {
    if (!this.routes) {
      throw new Error("Routes not initialized. Call navigateToRoot first.");
    }

    const categoryKey = `${resourceType} Endpoints`;
    method = method.toUpperCase();

    // Find the category
    if (!this.routes[categoryKey]) {
      return null;
    }

    // Find the endpoint with matching method
    const endpoint = this.routes[categoryKey].find(
      (route) => route.method === method
    );
    if (!endpoint) {
      return null;
    }

    // Replace parameters in URL
    let url = endpoint.url;
    for (const [key, value] of Object.entries(params)) {
      url = url.replace(`<${key}>`, value);
    }

    return url;
  }

  /**
   * Navigate to a resource using resource type and method
   *
   * @param {string} resourceType - The resource type (e.g., 'User', 'Group')
   * @param {string} method - The HTTP method (should be 'GET' for navigation)
   * @param {object} params - URL parameters
   * @returns {Promise<object>} The resource at the URL
   */
  async navigateToResource(resourceType, method, params = {}) {
    const endpoint = this.getResourceEndpoint(resourceType, method, params);
    if (!endpoint) {
      throw new Error(
        `Endpoint not found for ${resourceType} with method ${method}`
      );
    }

    return await this.navigateToUrl(endpoint);
  }

  /**
   * Execute an operation on a resource using resource type and method
   *
   * @param {string} resourceType - The resource type (e.g., 'User', 'Group')
   * @param {string} method - The HTTP method (e.g., 'POST', 'PUT', 'DELETE')
   * @param {object} params - URL parameters
   * @param {object} data - The data to send with the request
   * @returns {Promise<object>} The response from the operation
   */
  async executeResourceOperation(
    resourceType,
    method,
    params = {},
    data = null
  ) {
    const endpoint = this.getResourceEndpoint(resourceType, method, params);
    if (!endpoint) {
      throw new Error(
        `Endpoint not found for ${resourceType} with method ${method}`
      );
    }

    try {
      let response;

      switch (method.toUpperCase()) {
        case "POST":
          response = await this.axios.post(endpoint, data);
          break;
        case "PUT":
          response = await this.axios.put(endpoint, data);
          break;
        case "DELETE":
          response = await this.axios.delete(endpoint);
          break;
        case "GET":
        default:
          response = await this.axios.get(endpoint);
          break;
      }

      // Save API key if one is returned (for user creation)
      if (response.data && response.data.api_key) {
        this.setApiKey(response.data.api_key);
      }

      // Update current resource
      this.currentResource = response.data;
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get all available endpoints for a resource type
   *
   * @param {string} resourceType - The resource type (e.g., 'User', 'Group')
   * @returns {Array} The available endpoints for the resource
   */
  getResourceEndpoints(resourceType) {
    if (!this.routes) {
      throw new Error("Routes not initialized. Call navigateToRoot first.");
    }

    resourceType = resourceType.endsWith("s")
      ? resourceType
      : `${resourceType}s`;
    const categoryKey = `${resourceType} Endpoints`;

    return this.routes[categoryKey] || [];
  }

  /**
   * Navigate to a specific resource by URL
   *
   * @param {string} url - The URL to navigate to
   * @returns {Promise<object>} The resource at the URL
   */
  async navigateToUrl(url) {
    try {
      // Handle relative and absolute URLs
      const fullUrl = url.startsWith("http")
        ? url
        : url.startsWith("/")
        ? url
        : `${this.baseUrl}${url}`;

      const response = await this.axios.get(fullUrl);
      this.currentResource = response.data;
      return this.currentResource;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Follow a control link by name from the current resource
   *
   * @param {string} controlName - The name of the control to follow
   * @returns {Promise<object>} The resource reached by following the control
   */
  async followControl(controlName) {
    if (
      !this.currentResource ||
      !this.currentResource.controls ||
      !this.currentResource.controls[controlName]
    ) {
      throw new Error(`Control "${controlName}" not found in current resource`);
    }

    const control = this.currentResource.controls[controlName];
    return await this.navigateToUrl(control.href);
  }

  /**
   * Navigate to a named collection
   *
   * @param {string} collectionName - The name of the collection (e.g., 'users', 'expenses')
   * @returns {Promise<object>} The collection resource
   */
  async navigateToCollection(collectionName) {
    return await this.navigateToResource(collectionName, "GET");
  }

  /**
   * Get an item from a collection by ID
   *
   * @param {string} collectionName - The name of the collection
   * @param {string|number} itemId - The ID of the item to fetch
   * @returns {Promise<object>} The item resource
   */
  async getItem(collectionName, itemId) {
    const paramName = collectionName.endsWith("s")
      ? `${collectionName.slice(0, -1)}_id`
      : `${collectionName}_id`;

    const params = {};
    params[paramName] = itemId;

    return await this.navigateToResource(collectionName, "GET", params);
  }
  /**
   * Get the schema for a specific control
   *
   * @param {string} controlName - The name of the control to get schema for
   * @param {object} [resource=null] - Optional resource object, defaults to currentResource if not provided
   * @returns {object|null} The schema object or null if not found
   */
  getControlSchema(controlName, resource = null) {
    let targetResource = resource || this.currentResource;

    if (resource) {
      this.currentResource = resource;
      targetResource = resource["@controls"];
    }

    if (!targetResource) {
      throw new Error("No resource provided");
    }

    // Check if the control exists directly in the resource
    if (targetResource[controlName] && targetResource[controlName].schema) {
      return targetResource[controlName].schema;
    }

    // Check if the control exists in the controls object
    if (targetResource.controls && targetResource.controls[controlName]) {
      return targetResource.controls[controlName].schema || null;
    }

    return null;
  }

  /**
   * Get schema for a POST operation (create) on the current resource
   *
   * @param {object} [resource=null] - Optional resource object, defaults to currentResource if not provided
   * @returns {object|null} The schema for POST operations
   */
  getPostSchema(resource = null) {
    return this.getControlSchema("create", resource);
  }

  /**
   * Get schema for a PUT operation (update) on the current resource
   *
   * @param {object} [resource=null] - Optional resource object, defaults to currentResource if not provided
   * @returns {object|null} The schema for PUT operations
   */
  getPutSchema(resource = null) {
    return this.getControlSchema("update", resource);
  }

  /**
   * Extract schema from a response for a specific control
   *
   * @param {object} response - The API response containing control definitions
   * @param {string} controlName - The name of the control to get schema for
   * @returns {object|null} The schema object or null if not found
   */
  extractSchemaFromResponse(response, controlName) {
    if (!response) {
      throw new Error("No response provided");
    }

    return this.getControlSchema(controlName, response);
  }

  /**
   * Execute a control with data
   *
   * @param {string} controlName - The name of the control to execute
   * @param {object} data - The data to send with the request
   * @returns {Promise<object>} The response from executing the control
   */
  async executeControl(controlName, data = null) {
    if (
      !this.currentResource ||
      !this.currentResource["@controls"] ||
      !this.currentResource["@controls"][controlName]
    ) {
      throw new Error(`Control "${controlName}" not found in current resource`);
    }

    const control = this.currentResource["@controls"][controlName];
    const url = `/api${control.href}`;
    const method = control.method ? control.method.toLowerCase() : "get";

    try {
      let response;

      switch (method) {
        case "post":
          response = await this.axios.post(url, data);
          break;
        case "put":
          response = await this.axios.put(url, data);
          break;
        case "delete":
          response = await this.axios.delete(url);
          break;
        case "get":
        default:
          response = await this.axios.get(url);
          break;
      }

      // Save API key if one is returned (for user creation)
      if (response.data && response.data.api_key) {
        this.setApiKey(response.data.api_key);
      }

      // Update current resource
      this.currentResource = response.data;
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Create a new item in a collection
   *
   * @param {string} collectionName - The name of the collection
   * @param {object} data - The data for the new item
   * @returns {Promise<object>} The created item
   */
  async createItem(collectionName, data) {
    return await this.executeResourceOperation(
      collectionName,
      "POST",
      {},
      data
    );
  }

  /**
   * Update an item in a collection
   *
   * @param {string} collectionName - The name of the collection
   * @param {string|number} itemId - The ID of the item to update
   * @param {object} data - The data to update
   * @returns {Promise<object>} The updated item
   */
  async updateItem(collectionName, itemId, data) {
    const paramName = collectionName.endsWith("s")
      ? `${collectionName.slice(0, -1)}_id`
      : `${collectionName}_id`;

    const params = {};
    params[paramName] = itemId;

    return await this.executeResourceOperation(
      collectionName,
      "PUT",
      params,
      data
    );
  }

  /**
   * Delete an item from a collection
   *
   * @param {string} collectionName - The name of the collection
   * @param {string|number} itemId - The ID of the item to delete
   * @returns {Promise<object>} The response from the delete operation
   */
  async deleteItem(collectionName, itemId) {
    const paramName = collectionName.endsWith("s")
      ? `${collectionName.slice(0, -1)}_id`
      : `${collectionName}_id`;

    const params = {};
    params[paramName] = itemId;

    return await this.executeResourceOperation(
      collectionName,
      "DELETE",
      params
    );
  }

  /**
   * Get all items in the current collection
   *
   * @param {string} collectionProperty - The property in the response containing the collection
   * @returns {Array} The collection items
   */
  getCollectionItems(collectionProperty = null) {
    if (!this.currentResource) {
      throw new Error("No current resource");
    }

    // If collection property is specified, use it
    if (collectionProperty && this.currentResource[collectionProperty]) {
      return this.currentResource[collectionProperty];
    }

    // Try to find a collection property (first array in the resource)
    const arrayProperties = Object.entries(this.currentResource).filter(
      ([value]) => Array.isArray(value) && value.length > 0
    );

    if (arrayProperties.length > 0) {
      return arrayProperties[0][1];
    }

    return [];
  }

  /**
   * Handle errors from API requests
   *
   * @private
   * @param {Error} error - The error object
   */
  _handleError(error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const data = error.response.data;
      const message =
        data && data.message ? data.message : error.response.statusText;

      const customError = new Error(message);
      customError.status = error.response.status;
      customError.data = data;
      throw customError;
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error("No response received from server");
    } else {
      // Something happened in setting up the request that triggered an Error
      throw error;
    }
  }
}

export default HypermediaClient;
