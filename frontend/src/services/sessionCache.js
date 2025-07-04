class SessionAPICache {
    constructor(options = {}) {
      this.memoryCache = new Map();
      this.sessionStorage = window.sessionStorage;
      this.cachePrefix = options.prefix || 'stock_api_';
      this.maxMemoryItems = options.maxMemoryItems || 1000;
      this.debug = options.debug || false;
    }
  
    generateCacheKey(endpoint, params = {}) {
      const sortedParams = Object.keys(params)
        .sort()
        .map(key => `${key}=${encodeURIComponent(params[key])}`)
        .join('&');
      return `${this.cachePrefix}${endpoint}${sortedParams ? '?' + sortedParams : ''}`;
    }
  
    async get(endpoint, params = {}) {
      const cacheKey = this.generateCacheKey(endpoint, params);
      
      // Check memory cache first (fastest)
      if (this.memoryCache.has(cacheKey)) {
        if (this.debug) console.log('🎯 Cache HIT (memory):', cacheKey);
        return this.memoryCache.get(cacheKey);
      }
      
      // Check sessionStorage (survives page refresh)
      try {
        const sessionData = this.sessionStorage.getItem(cacheKey);
        if (sessionData) {
          const parsed = JSON.parse(sessionData);
          // Restore to memory cache for faster subsequent access
          this.memoryCache.set(cacheKey, parsed);
          if (this.debug) console.log('🎯 Cache HIT (session):', cacheKey);
          return parsed;
        }
      } catch (error) {
        console.warn('Error reading from sessionStorage:', error);
        this.sessionStorage.removeItem(cacheKey);
      }
      
      if (this.debug) console.log('❌ Cache MISS:', cacheKey);
      return null;
    }
  
    set(endpoint, params = {}, data) {
      const cacheKey = this.generateCacheKey(endpoint, params);
      
      // Store in memory cache
      this.memoryCache.set(cacheKey, data);
      
      // Store in sessionStorage for persistence
      try {
        this.sessionStorage.setItem(cacheKey, JSON.stringify(data));
        if (this.debug) console.log('💾 Cache SET:', cacheKey);
      } catch (error) {
        if (error.name === 'QuotaExceededError') {
          this.clearOldestEntries();
          try {
            this.sessionStorage.setItem(cacheKey, JSON.stringify(data));
          } catch (secondError) {
            console.warn('Unable to cache in sessionStorage after cleanup:', secondError);
          }
        } else {
          console.warn('Error writing to sessionStorage:', error);
        }
      }
      
      // Prevent memory cache from growing too large
      if (this.memoryCache.size > this.maxMemoryItems) {
        const firstKey = this.memoryCache.keys().next().value;
        this.memoryCache.delete(firstKey);
      }
    }
  
    clearOldestEntries() {
      const keys = Object.keys(this.sessionStorage)
        .filter(key => key.startsWith(this.cachePrefix));
      
      // Remove oldest 25% of entries
      const toRemove = Math.ceil(keys.length * 0.25);
      keys.slice(0, toRemove).forEach(key => {
        this.sessionStorage.removeItem(key);
      });
      
      console.log(`Cleared ${toRemove} old cache entries`);
    }
  
    clearAll() {
      this.memoryCache.clear();
      Object.keys(this.sessionStorage)
        .filter(key => key.startsWith(this.cachePrefix))
        .forEach(key => this.sessionStorage.removeItem(key));
      
      if (this.debug) console.log('🧹 Cache cleared');
    }
  
    getCacheStats() {
      const sessionKeys = Object.keys(this.sessionStorage)
        .filter(key => key.startsWith(this.cachePrefix));
      
      return {
        memoryEntries: this.memoryCache.size,
        sessionEntries: sessionKeys.length,
        totalMemorySize: this._estimateMemorySize(),
        sessionStorageUsed: this._estimateSessionStorageSize()
      };
    }
  
    _estimateMemorySize() {
      let size = 0;
      this.memoryCache.forEach((value, key) => {
        size += JSON.stringify(value).length + key.length;
      });
      return size;
    }
  
    _estimateSessionStorageSize() {
      let size = 0;
      Object.keys(this.sessionStorage)
        .filter(key => key.startsWith(this.cachePrefix))
        .forEach(key => {
          size += key.length + (this.sessionStorage.getItem(key)?.length || 0);
        });
      return size;
    }
  }
  
  export default SessionAPICache;