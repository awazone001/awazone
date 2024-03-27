!function(){
    let classes = ["fs-sm", "d-inline-block", "fw-medium", "animated", "fadeIn", "bg-body-light", "border-3", "px-3", "py-2", "mb-2", "shadow-sm", "mw-100"];
    let senderClasses = ["border-end", "border-primary", "rounded-start", "text-start"];
    let receiverClasses = ["border-start", "border-dark", "rounded-end"];
    let infoClasses = ["fs-sm", "text-muted", "animated", "fadeIn", "my-2"];
  
    class Chat {
      static initChat() {
        let self = this;
        
        document.querySelectorAll(".js-chat-form form").forEach((form) => {
          form.addEventListener("submit", (event) => {
            event.preventDefault();
            
            let input = form.querySelector(".js-chat-input");
            let targetChatId = parseInt(input.dataset.targetChatId);
            let message = input.value.trim();
            
            if (message !== '') {
              self.chatAddMessage(targetChatId, message, "self");
              input.value = '';
            }
          });
        });
      }
      
      static chatAddHeader(chatId, text, sender) {
        let chatMessages = document.querySelector('.js-chat-messages[data-chat-id="' + chatId + '"]');
        
        if (text && chatMessages !== null) {
          let headerDiv = document.createElement("div");
          let textDiv = document.createElement("div");
          
          infoClasses.forEach((className) => {
            textDiv.classList.add(className);
          });
          
          if (sender === "self") {
            textDiv.classList.add("text-end");
            headerDiv.classList.add("ms-4");
          }
          
          textDiv.innerText = text;
          headerDiv.appendChild(textDiv);
          chatMessages.appendChild(headerDiv);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      }
      
      static chatAddMessage(chatId, message, sender) {
        let chatMessages = document.querySelector('.js-chat-messages[data-chat-id="' + chatId + '"]');
        
        if (message && chatMessages !== null) {
          let messageDiv = document.createElement("div");
          let textDiv = document.createElement("div");
          
          classes.forEach((className) => {
            textDiv.classList.add(className);
          });
          
          if (sender === "self") {
            messageDiv.classList.add("text-end");
            messageDiv.classList.add("ms-4");
            senderClasses.forEach((className) => {
              textDiv.classList.add(className);
            });
          } else {
            messageDiv.classList.add("me-4");
            receiverClasses.forEach((className) => {
              textDiv.classList.add(className);
            });
          }
          
          textDiv.innerText = message;
          messageDiv.appendChild(textDiv);
          chatMessages.appendChild(messageDiv);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      }
      
      static init() {
        this.initChat();
      }
      
      static addHeader(chatId, text, sender) {
        let info = arguments.length > 2 && void 0 !== arguments[2] ? arguments[2] : "";
        this.chatAddHeader(chatId, text, sender, info);
      }
      
      static addMessage(chatId, message, sender) {
        let info = arguments.length > 3 && void 0 !== arguments[3] ? arguments[3] : "";
        this.chatAddMessage(chatId, message, sender, info);
      }
    }
    
    Dashmix.onLoad(() => {
      Chat.init();
      window.Chat = Chat;
    });
  }();
  