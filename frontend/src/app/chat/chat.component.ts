import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../services/chat.service';

interface ChatMessage {
    text: string;
    isUser: boolean;
}

@Component({
    selector: 'app-chat',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './chat.component.html',
    styleUrls: ['./chat.component.css']
})
export class ChatComponent {
    userInput: string = '';
    messages: ChatMessage[] = [];
    isLoading: boolean = false;

    constructor(private chatService: ChatService) { }

    sendMessage() {
        if (!this.userInput.trim()) return;

        const messageText = this.userInput;
        this.messages.push({ text: messageText, isUser: true });
        this.userInput = '';
        this.isLoading = true;

        this.chatService.sendMessage(messageText).subscribe({
            next: (response) => {
                this.messages.push({ text: response.response, isUser: false });
                this.isLoading = false;
            },
            error: (error) => {
                console.error('Error sending message:', error);
                this.messages.push({ text: 'Error connecting to AI. Please try again.', isUser: false });
                this.isLoading = false;
            }
        });
    }
}
